# Famsplit
Expense tracking application

## Setting up application
The application is dockerized. Running it brings up 2 containers - application and mysql
1. Copy `docker-compose.yml` file
   ```
   version: '3'

    services:
      db:
        image: mysql/mysql-server:5.7
        ports:
          - "3306:3306"
        environment:
          - MYSQL_ROOT_PASSWORD=joeydoesntsharefood
          - MYSQL_DATABASE=famsplit
          - MYSQL_ROOT_HOST=%
      web:
        image: gauravkulkarni96/famsplit:latest
        ports:
          - "8000:8000"
        depends_on:
          - db
   ```
  
2. run `docker-compose up`

NOTE - If you name the file anything apart from `docker-compose.yml`, use command `docker-compose -f <filename> up`

## Supported APIs
### Create user
```
API - POST http://127.0.0.1:8000/create_user/

Sample JSON request data - 
{
    "username":"gaurav1",
    "password":"root@123",
    "email":"gaurav1@test.com"
}

Sample JSON response - 
{
    "message": "User created successfully!"
}
```
### Login
Access token received is to be used in other requests as Bearer token. Validity of access token is 24 hours. It can be refreshed using refresh token for 2 days post which login is required again.
```
API - POST http://127.0.0.1:8000/api/token/

Sample JSON request data - 
{
    "username":"gaurav1",
    "password":"root@123",
}

Sample JSON response - `
{
    "refresh": "<refresh_token>",
    "access": "<access_token>"
}
```
### Create Group
```
API - POST http://127.0.0.1:8000/group/create/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
  "groupname": "party"
}

Sample JSON response - 
{
    "message": "Group created successfully!"
}
```
### Add user to group
```
API - POST http://127.0.0.1:8000/group/adduser/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "groupname":"party",
    "username":"gauravtest2"
}

Sample JSON response - 
{
    "error": "Member added successfully!"
}
```
### Remove user from group
```
API - POST http://127.0.0.1:8000/group/removeuser/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "username": "gaurav1",
    "groupname": "party"
}

Sample JSON response - 
{
    "message": "Member removed successfully!"
}
```
### Add Bill
Note -
- `split_type` - `equal`,`fixed`,`percentage`
- `split_data` not mandatory when bill needs to be split `equal`ly between all group members. For splitting `equal`ly between a subset of members the values in json can be `0` eg -`"split_data": {"gauravtest2": 0, "gauravtest1": 0, "gauravtest3": 0 }`
```
API - POST http://127.0.0.1:8000/group/addbill/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "groupname": "party",
    "title": "pizza",
    "amount": 550,
    "split_type": "fixed",
    "split_data": {
        "gauravtest2": 150,
        "gauravtest1": 350,
        "gauravtest3": 50
    },
    "pay_data": {
        "gauravtest": 400,
        "gauravtest1": 150
    }
}

Sample JSON response - 
{
    "message": "Bill added successfully!"
}
```
### Edit Bill
Note - same as <a href="#add-bill">Add Bill</a>
```
API - POST http://127.0.0.1:8000/group/editbill/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "groupname": "party",
    "title": "pizza",
    "amount": 550,
    "split_type": "fixed",
    "split_data": {
        "gauravtest2": 150,
        "gauravtest1": 350,
        "gauravtest3": 50
    },
    "pay_data": {
        "gauravtest": 450,
        "gauravtest1": 100
    }
}

Sample JSON response - 
{
    "message": "Bill updated successfully!"
}
```
### Add comment/image on bill
```
API - POST http://127.0.0.1:8000/group/billcomment/ header 'Authorization: Bearer <access_token>'

Sample form request data - 
bill_id:24
image:<file_upload>
comment:dominos pizza

Sample JSON response - 
{
    "message": "Comment added to bill successfully!"
}
```
### Get group Balance
```
API - POST http://127.0.0.1:8000/group/balance/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "groupname": "party"
}

Sample JSON response - 
{
    "gaurav1": 33.33
}
```
### Get global user balance
```
API - POST http://127.0.0.1:8000/user/balance/ header 'Authorization: Bearer <access_token>'

Sample JSON response - 
{
    "gaurav1": 33.33
}
```
### Settle group balance
```
API - POST http://127.0.0.1:8000/group/settle/ header 'Authorization: Bearer <access_token>'

Sample JSON request data - 
{
    "groupname":"trip",
    "username":"gauravtest2"
}

Sample JSON response - 
{
    "message": "Balance Settled!"
}
```
### Add user profile picture
```
API - POST http://127.0.0.1:8000/user/addpicture/ header 'Authorization: Bearer <access_token>'

Sample request data - 
image:<file_upload>

Sample JSON response - 
{
    "message": "User profile pic updated successfully!",
    "image": "/media/uploads/fb_dp_rBMU0TZ.jpg"
}
```
### Add group profile picture
```
API - POST http://127.0.0.1:8000/group/addpicture/ header 'Authorization: Bearer <access_token>'

Sample request data - 
groupname:party
image:<file_upload>

Sample JSON response - 
{
    "message": "Group icon updated successfully!",
    "image": "/media/uploads/dp2.jpg"
}
```
