# TODO

- [x] Create the DB
- [x] Create endpoints
  - [x] refresh db
  - [x] paginate transactions
  - [ ] stats
    - [ ] Given a string, how much money do the matches add up? How many matches are there?
            Think of UBER, how much have you spent and how many times total you have done a transaction like that.

# LATEST

- [ ] Return the entire list in the response.
  - [ ] Use redis or memcached to keep a cached list of transactions and make the system faster.
- [ ] Scheduled refresh of the DB
