/* ExploreDC : Database Schema (MySQL 8)
   CS 5614 - Introduction to Database Systems, Summer 2026
   Author: Marwa Bahr
   Creates the exploredc schema and all 8 tables with
   PK, FK, NOT NULL, UNIQUE, and CHECK constraints.
   Passwords are stored as SHA2-256 hashes, never plain text. */

DROP DATABASE IF EXISTS exploredc;
CREATE DATABASE exploredc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE exploredc;

CREATE TABLE app_user (
    UserID        INT           NOT NULL AUTO_INCREMENT,
    Username      VARCHAR(30)   NOT NULL,
    Email         VARCHAR(100)  NOT NULL,
    PasswordHash  CHAR(64)      NOT NULL,
    Role          VARCHAR(10)   NOT NULL DEFAULT 'member',
    CONSTRAINT pk_user       PRIMARY KEY (UserID),
    CONSTRAINT uq_user_name  UNIQUE (Username),
    CONSTRAINT uq_user_email UNIQUE (Email),
    CONSTRAINT ck_user_role  CHECK (Role IN ('admin', 'member')),
    CONSTRAINT ck_user_email CHECK (Email LIKE '%_@_%._%')
);

CREATE TABLE museum (
    MuseumID     INT           NOT NULL AUTO_INCREMENT,
    Name         VARCHAR(100)  NOT NULL,
    Address      VARCHAR(150)  NOT NULL,
    Description  TEXT          NULL,
    CONSTRAINT pk_museum      PRIMARY KEY (MuseumID),
    CONSTRAINT uq_museum_name UNIQUE (Name)
);

/* EXHIBIT is a weak entity owned by MUSEUM: PK = owner key + partial key */
CREATE TABLE exhibit (
    MuseumID     INT           NOT NULL,
    ExhibitName  VARCHAR(100)  NOT NULL,
    Location     VARCHAR(80)   NOT NULL,
    CONSTRAINT pk_exhibit PRIMARY KEY (MuseumID, ExhibitName),
    CONSTRAINT fk_exhibit_museum FOREIGN KEY (MuseumID)
        REFERENCES museum (MuseumID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE category (
    CategoryID  INT          NOT NULL AUTO_INCREMENT,
    Name        VARCHAR(60)  NOT NULL,
    CONSTRAINT pk_category      PRIMARY KEY (CategoryID),
    CONSTRAINT uq_category_name UNIQUE (Name)
);

/* FKs are NOT NULL: every artifact is in exactly one exhibit and one category */
CREATE TABLE artifact (
    ArtifactID   INT           NOT NULL AUTO_INCREMENT,
    Title        VARCHAR(120)  NOT NULL,
    Creator      VARCHAR(100)  NULL,
    Year         SMALLINT      NULL,
    MuseumID     INT           NOT NULL,
    ExhibitName  VARCHAR(100)  NOT NULL,
    CategoryID   INT           NOT NULL,
    CONSTRAINT pk_artifact PRIMARY KEY (ArtifactID),
    CONSTRAINT ck_artifact_year CHECK (Year IS NULL OR Year BETWEEN -3000 AND 2026),
    CONSTRAINT fk_artifact_exhibit FOREIGN KEY (MuseumID, ExhibitName)
        REFERENCES exhibit (MuseumID, ExhibitName)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_artifact_category FOREIGN KEY (CategoryID)
        REFERENCES category (CategoryID)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE visit (
    VisitID    INT           NOT NULL AUTO_INCREMENT,
    VisitDate  DATE          NOT NULL,
    Notes      VARCHAR(500)  NULL,
    UserID     INT           NOT NULL,
    MuseumID   INT           NOT NULL,
    CONSTRAINT pk_visit PRIMARY KEY (VisitID),
    CONSTRAINT fk_visit_user FOREIGN KEY (UserID)
        REFERENCES app_user (UserID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_visit_museum FOREIGN KEY (MuseumID)
        REFERENCES museum (MuseumID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

/* uq_review_user_museum: at most one review per user per museum */
CREATE TABLE review (
    ReviewID    INT           NOT NULL AUTO_INCREMENT,
    Rating      TINYINT       NOT NULL,
    Comment     VARCHAR(1000) NULL,
    ReviewDate  DATE          NOT NULL,
    UserID      INT           NOT NULL,
    MuseumID    INT           NOT NULL,
    CONSTRAINT pk_review PRIMARY KEY (ReviewID),
    CONSTRAINT ck_review_rating CHECK (Rating BETWEEN 1 AND 5),
    CONSTRAINT uq_review_user_museum UNIQUE (UserID, MuseumID),
    CONSTRAINT fk_review_user FOREIGN KEY (UserID)
        REFERENCES app_user (UserID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_review_museum FOREIGN KEY (MuseumID)
        REFERENCES museum (MuseumID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

/* M:N between USER and ARTIFACT */
CREATE TABLE must_see (
    UserID     INT   NOT NULL,
    ArtifactID INT   NOT NULL,
    DateAdded  DATE  NOT NULL,
    CONSTRAINT pk_must_see PRIMARY KEY (UserID, ArtifactID),
    CONSTRAINT fk_mustsee_user FOREIGN KEY (UserID)
        REFERENCES app_user (UserID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_mustsee_artifact FOREIGN KEY (ArtifactID)
        REFERENCES artifact (ArtifactID)
        ON UPDATE CASCADE ON DELETE CASCADE
);
