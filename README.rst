Statsite
========

This is a stats aggregation server. By default, Statsite flushes data
to `Graphite <http://graphite.wikidot.com/>`_. Statsite is based heavily
on `Etsy's Graphite <github.com/etsy/statsd>`_.

Features
--------

* Basic key/value metrics
* Send timer data, Statsite will calculate:
  - Mean
  - Min/Max
  - Standard deviation
  - All the above metrics for a specific percentile of information
* Send counters that Statsite will aggregate
* Send a sample rate with counters and Statsite will take that into
  account when aggregating.

Install
-------

Install Statsite from PyPi::

    pip install statsite

Or download and install from source::

    python setup.py install

Usage
-----

Statsite preferably should be configured using a file, although all
configuration parameters can be set via the command line as well.
Here is an example configuration file:

::

    # Settings for the "collector" which is the UDP listener
    [collector]
    host = 0.0.0.0
    port = 8125

    # Specify settings for the metrics "store" which is where graphite is
    [store]
    host = 0.0.0.0
    port = 2003

Then run statsite, pointing it to that file (assuming `/etc` right now)::

    statsite -c /etc/statsite.conf

Protocol
--------

By default, Statsite will listen for UDP packets, which makes it extremely
cheap for your application to fire and forget packets to the server. A message
looks like the following (where the flag is optional)::

    key:value|type[|@flag]

Messages should be separated by newlines (`\n`) if multiple are sent in the
same packet.

Currently supported message types:

* `kv` - Simple Key/Value. If a flag is given, it is considered the timestamp
  of the key/value pair.
* `ms` - Timer. If a flag is given, it is considered the sampling rate of the
  timer.
* `c` - Counter. After the flush interval, the counters of the same key are
  aggregated and this is sent to the store.

Examples:

The following is a simple key/value pair, in this case reporting how many
queries we've seen in the last second on MySQL::

    mysql.queries:1381|kv|@1313107325

The following is a timer, timing the response speed of an API call::

    api.session_created:114|ms

The following is another timer, but this time saying we sample this data in
1/10th of the API requests.

::

    api.session_created:114|ms|@0.1

The next example is increments the "rewards" counter by 1::

    rewards:1|c

And this example decrements the "inventory" counter by 7::

    inventory:-7|c

As said earlier, multiple messages can be joined together by newlines.
