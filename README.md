# Sawtooth Simple Supply

Sawtooth Simple Supply is a basic example of a distributed supply-chain
application. It provides asset transfer with location tracking, which allows
users to transfer assets and track them as they move through a supply chain.

Sawtooth Simple Supply is built on Hyperledger Sawtooth, an enterprise
blockchain platform. To learn more about Hyperledger Sawtooth, see the
[sawtooth-core repository](https://github.com/hyperledger/sawtooth-core) and the
[Hyperledger Sawtooth documentation](https://sawtooth.hyperledger.org/docs/).

The Simple Supply components in this repository include:

- A transaction processor that handles the Simple Supply transaction logic

- A custom REST API that provides HTTP/JSON endpoints for querying blockchain
  data, creates batches and transactions, and manages user information

- An event subscriber that parses blockchain events and stores data in a local,
  off-chain reporting database

- A simple client web app, Curator, that uses Simple Supply to track artwork
  loans between museums, galleries, and private owners

## Usage


Clone the Simple Supply repository, then make sure that you have the `docker`
and `docker-compose` commands installed on your machine.

To run the application, navigate to the project's root directory, then use
this command:

```bash
docker-compose up
```

This command starts all Simple Supply components in separate containers.

The available HTTP endpoints are:
- Client: **http://localhost:8040**
- Simple Supply REST API: **http://localhost:8000**
- PostgreSQL Adminer: **http://localhost:8080**
- Sawtooth REST API: **http://localhost:8008**

## License

The Sawtooth Simple Supply software and course material in the
[course_modules](course_modules) subdirectory is licensed under a
Creative Commons Attribution 4.0 International License.  You may obtain a copy
of the license at: http://creativecommons.org/licenses/by/4.0/.
