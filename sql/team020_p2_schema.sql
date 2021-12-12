-- CREATE USER 'newuser'@'localhost' IDENTIFIED BY 'password';
CREATE USER IF NOT EXISTS 'gatechUser'@'localhost' IDENTIFIED BY 'gatech123';

-- DROP DATABASE IF EXISTS `cs6400_fa21_team020`;
SET default_storage_engine=InnoDB;
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cs6400_fa21_team020;

GRANT SELECT, INSERT, UPDATE, DELETE, FILE ON *.* TO 'gatechUser'@'localhost';
GRANT ALL PRIVILEGES ON `gatechuser`.* TO 'gatechUser'@'localhost';
GRANT ALL PRIVILEGES ON `cs6400_fa21_team020`.* TO 'gatechUser'@'localhost';
FLUSH PRIVILEGES;


-- Tables
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS UserRole;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS IndividualPerson;
DROP TABLE IF EXISTS Business;
DROP TABLE IF EXISTS Manufacturer;
DROP TABLE IF EXISTS Vehicle;
DROP TABLE IF EXISTS VehicleColor;
DROP TABLE IF EXISTS Car;
DROP TABLE IF EXISTS Convertible;
DROP TABLE IF EXISTS Truck;
DROP TABLE IF EXISTS VanMinivan;
DROP TABLE IF EXISTS SUV;
DROP TABLE IF EXISTS Repair;
DROP TABLE IF EXISTS Part;

CREATE TABLE User(
  Username VARCHAR(250) Not NULL,
  Fname VARCHAR(120) NOT NULL,
  Lname VARCHAR(120) NOT NULL,
  Password VARCHAR(250) NOT NULL,
  PRIMARY KEY (Username)
);
CREATE TABLE UserRole(
  Username VARCHAR(250) Not NULL,
  Role VARCHAR(120) NOT NULL,
  PRIMARY KEY (Username, Role),
  FOREIGN KEY (Username) REFERENCES User(Username)
);
CREATE TABLE Customer(
  CustomerID int(16) UNSIGNED NOT NULL AUTO_INCREMENT,
  Email varchar(250),
  Street varchar(200) NOT NULL,
  City varchar(200) NOT NULL,
  State varchar(200) NOT NULL,
  Zipcode varchar(20) NOT NULL,
  Phone_number varchar(20) NOT NULL,
  PRIMARY KEY (CustomerID)
);
CREATE TABLE IndividualPerson(
  ID varchar(100) NOT NULL,
  Fname varchar(100) NOT NULL,
  Lname varchar(100) NOT NULL,
  CustomerID int(16) unsigned NOT NULL,
  PRIMARY KEY(ID),
  FOREIGN KEY (CustomerID)
        REFERENCES Customer(CustomerID)
        ON DELETE CASCADE
);

CREATE TABLE Business(
  Tax_ID varchar(100) NOT NULL,
  Title varchar(250) NOT NULL,
  Business_name varchar(250) NOT NULL,
  Fname varchar(250) NOT NULL,
  Lname varchar(250) NOT NULL,
  CustomerID int(16) unsigned NOT NULL,
  PRIMARY KEY(Tax_ID),
  FOREIGN KEY (CustomerID)
        REFERENCES Customer(CustomerID)
        ON DELETE CASCADE
);
CREATE TABLE Manufacturer(
  Manufacturer_name varchar(200) NOT NULL,
  PRIMARY KEY(Manufacturer_name)
);

CREATE TABLE Vehicle(
  VIN varchar(250) NOT NULL,
  Manufacturer_name varchar(200) NOT NULL,
  Model_name varchar(100) NOT NULL,
  Model_year int(4)  NOT NULL,
  Invoice_price DECIMAL(19,2) NOT NULL,
  Description varchar(250),
  CustomerID int(16) unsigned,
  Sold_date  date,
  Sold_price DECIMAL(19,2),
  Add_date date NOT NULL,
  Type varchar(250) NOT NULL,
  Sold_by varchar(250),
  Added_by varchar(250),
  PRIMARY KEY (VIN),
  FOREIGN key(Manufacturer_name) REFERENCES Manufacturer(Manufacturer_name),
  FOREIGN key(CustomerID) REFERENCES Customer(CustomerID),
  FOREIGN key(Sold_by) REFERENCES User(Username),
  FOREIGN key(Added_by) REFERENCES User(Username)
);
CREATE TABLE VehicleColor (
  VIN varchar(250) NOT NULL,
  Color varchar(120) NOT NULL,
  PRIMARY KEY (VIN, Color),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
);

CREATE TABLE Car (
  VIN varchar(250) NOT NULL,
  Num_of_doors int(16) NOT NULL,
  PRIMARY KEY (VIN),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
  
);
CREATE TABLE Convertible (
  VIN varchar(250) NOT NULL,
  Roof_type varchar(100) NOT NULL,
  Back_seat_count int(16)  NOT NULL,
  PRIMARY KEY (VIN),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
);

CREATE TABLE Truck (
  VIN varchar(250) NOT NULL,
  Cargo_capacity varchar(100) NOT NULL,
  Num_of_rear_axies int(16)  NOT NULL,
  Cargo_cover_type varchar(100),
  PRIMARY KEY (VIN),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
);

CREATE TABLE VanMinivan (
  VIN varchar(250) NOT NULL,
  Has_back_door tinyint(1), 
  PRIMARY KEY (VIN),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
);

CREATE TABLE SUV (
  VIN varchar(250) NOT NULL,
  Drivetrain_type varchar(100) NOT NULL,
  Num_of_cupholders int(16) unsigned NOT NULL,
  PRIMARY KEY (VIN),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN)
);

CREATE TABLE Repair (  
  VIN varchar(250) NOT NULL,
  CustomerID INT(16) unsigned NOT NULL,
  Start_date DATE NOT NULL,
  Labor_fee DECIMAL(19,2),
  Description VARCHAR(250) NULL,
  Complete_date DATE NULL,
  Odometer INT NOT NULL,
  Username varchar(250) NOT NULL,
  PRIMARY KEY (VIN, CustomerID, Start_date),
  FOREIGN KEY(CustomerID) REFERENCES Customer(CustomerID),
  FOREIGN KEY(VIN) REFERENCES Vehicle(VIN),
  FOREIGN KEY(Username) REFERENCES User(Username)
);
Create TABLE Part (
  VIN varchar(250) NOT NULL,
  CustomerID INT(16) unsigned NOT NULL,
  Start_date DATE NOT NULL,
  Vendor_name VARCHAR(250) NOT NULL,
  Part_price DECIMAL(19,2) NOT NULL,
  Part_number VARCHAR(250) NOT NULL,
  Quantity INT NOT NULL,
  PRIMARY KEY(VIN, CustomerID, Start_date, Part_number),
  FOREIGN KEY(VIN, CustomerID, Start_date) REFERENCES Repair(VIN, CustomerID, Start_date)
);
-- Constraints   Foreign Keys: FK_ChildTable_childColumn_ParentTable_parentColumn

ALTER TABLE IndividualPerson
    ADD CONSTRAINT fk_IndividualPerson_CustomerID_Customer_CustomerID FOREIGN KEY (CustomerID) REFERENCES Customer (CustomerID) ON DELETE CASCADE ON UPDATE CASCADE;  
ALTER TABLE Business
    ADD CONSTRAINT fk_Business_CustomerID_Customer_CustomerID FOREIGN KEY (CustomerID) REFERENCES Customer (CustomerID) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE Vehicle
    ADD CONSTRAINT fk_Vehicle_Manufacturer_name_Manufacturer_Manufacturer_name FOREIGN key (Manufacturer_name) REFERENCES Manufacturer (Manufacturer_name),
    ADD CONSTRAINT fk_Vehicle_CustomerID_Customer_CustomerID FOREIGN key (CustomerID) REFERENCES Customer (CustomerID),
    ADD CONSTRAINT fk_Vehicle_Sold_by_User_Username FOREIGN KEY (Sold_by) REFERENCES User (Username),
    ADD CONSTRAINT fk_Vehicle_Added_by_User_Username FOREIGN KEY (Added_by) REFERENCES User (Username);
ALTER TABLE VehicleColor
    ADD CONSTRAINT fk_VehicleColor_VIN_Vehicle_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE UserRole
    ADD CONSTRAINT fk_User_Username_UserRole_Username FOREIGN KEY (Username) REFERENCES User(Username) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE Car
    ADD CONSTRAINT fk_Car_VIN_Vehcile_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE Convertible
    ADD CONSTRAINT fk_Convertible_VIN_Vehcile_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE Truck
    ADD CONSTRAINT fk_Truck_VIN_Vehcile_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE VanMinivan
    ADD CONSTRAINT fk_VanMinivan_VIN_Vehcile_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE SUV
    ADD CONSTRAINT fk_SUV_VIN_Vehcile_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER Table Repair
    ADD CONSTRAINT fk_Repair_CustomerID_Customer_CustomerID FOREIGN KEY (CustomerID) REFERENCES Customer (CustomerID),
    ADD CONSTRAINT fk_Repair_VIN_Vehicle_VIN FOREIGN KEY (VIN) REFERENCES Vehicle (VIN),
    ADD CONSTRAINT fk_Repair_Username_User_Username FOREIGN KEY (Username) REFERENCES User (Username);
ALTER Table Part
    ADD CONSTRAINT fk_Part_Repair FOREIGN KEY (VIN, CustomerID, Start_date) REFERENCES Repair (VIN, CustomerID, Start_date) ON DELETE CASCADE ON UPDATE CASCADE;