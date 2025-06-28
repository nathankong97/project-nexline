-- Stores distinct train numbers seen per service date.
CREATE TABLE IF NOT EXISTS train_numbers (
    date_scraped DATE,
    train_no     VARCHAR,
    PRIMARY KEY (date_scraped, train_no)
);