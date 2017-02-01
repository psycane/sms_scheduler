create database sms_scheduler;
use sms_scheduler;
create table details(
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	phone_no VARCHAR(255) NOT NULL,
	country_code INT NOT NULL
);
