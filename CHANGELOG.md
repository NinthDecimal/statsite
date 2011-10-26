## 0.4.0 (October 26, 2011)

  - Multiple "-c" configuration files can be passed to `statsite`.
  - If a configuration file doesn't exist or contains a parse
    error, and error will be raised.
  - Try to increase socket buffer size for UDP to avoid packet
    loss when the buffer is full during high load.
  - Prefix key-value entries with "kv"

## 0.3.0 (September 1, 2011)

  - Class to load for various components can be passed to the
    configuration as a string.

## 0.2.0 (August 31, 2011)

  - Add a TCP "aliveness_check" option for easier monitoring.
  - Fix off-by-one issue in calculating percentile statistics.

## 0.1.0 (August 16, 2011)

  - Initial release
