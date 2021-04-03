# pops-network-validators-data
This project is building an API gateway exposing the POPS network validator data


## build the image
docker build --tag network-validator-data .

## run the image
docker run -p 80:5000 --rm network-validator-data


## TODOs

- swagger API documentation :  https://michal.karzynski.pl/blog/2016/06/19/building-beautiful-restful-apis-using-flask-swagger-ui-flask-restplus/ 

- dynamic capture of all the network data of the validator
