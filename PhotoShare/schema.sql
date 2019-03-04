CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE `photoshare`.`Users` (
    user_id int  AUTO_INCREMENT,
    email varchar(255) NOT NULL UNIQUE,
    password varchar(255) NOT NULL,
    firstName varchar(255) NOT NULL,
    lastName varchar(255) NOT NULL,
    hometown varchar(255),
    gender ENUM('M', 'F'),
    dateOfBirth varchar(255) NOT NULL,
    PRIMARY KEY (user_id)
);

CREATE TABLE `photoshare`.`Albums`
(
  album_id int AUTO_INCREMENT,
  albumName varchar(255),
  -- date_created DATE,
  user_id int,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  PRIMARY KEY (album_id),
  UNIQUE KEY albumid (user_id, albumName)
);

CREATE TABLE `photoshare`.`Pictures`
(
  picture_id int  AUTO_INCREMENT,
  -- imgdata varchar(255) NOT NULL,
  imgdata longblob,
  user_id int,
  caption varchar(255),
  album_id int,
  INDEX upid_idx (user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  PRIMARY KEY (picture_id)
);

CREATE TABLE `photoshare`.`Tags`
(
  word varchar(255),
  picture_id int,
  PRIMARY KEY (word, picture_id)
);

CREATE TABLE  `photoshare`.`Friends`
(
 user_id int NOT NULL,
 friend_id int NOT NULL,
 FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
 FOREIGN KEY (friend_id) REFERENCES Users(user_id) ON DELETE CASCADE,
 PRIMARY KEY  (user_id, friend_id)
);

CREATE TABLE  `photoshare`.`Comments`
(
  cid INT AUTO_INCREMENT,
  content varchar(255),
  owner int DEFAULT '0',
  picture_id int NOT NULL,
  FOREIGN KEY (owner) REFERENCES Users(user_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  PRIMARY KEY (cid)
);

CREATE TABLE `photoshare`.`Likes`
(
  like_id int AUTO_INCREMENT,
  picture_id int,
  user_id int,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  PRIMARY KEY (like_id)
);


INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('test1@bu.edu', 'test', 'Joe', 'Zhou', 'town', 'M', '2000-12-31');
INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('test2@bu.edu', 'test', 'Sma', 'To', 'town', 'F', '2000-12-31');
INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('test3@bu.edu', 'test', 'Kanad', 'B', 'town', 'M', '2000-12-31');
INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('test4@bu.edu', 'test', 'Ekaterina', 'P',  'town', 'F', '2000-12-31');

INSERT INTO Albums (albumName, user_id) VALUES ('album1', 1);
INSERT INTO Albums (albumName, user_id) VALUES ('album2', 1);
INSERT INTO Albums (albumName, user_id) VALUES ('album3', 2);