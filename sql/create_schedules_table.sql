CREATE TABLE IF NOT EXISTS schedules (
  date_scraped DATE,
  train_no    VARCHAR,
  station     VARCHAR,
  sched_time  TIME,       -- e.g. 15:08
  est_time    TIME,       -- e.g. 15:11
  act_time    VARCHAR,    -- allows “na” or a time string like “15:12”
  PRIMARY KEY (date_scraped, train_no, station)
);
