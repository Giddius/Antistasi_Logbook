=============================
Database
=============================





Why SQLite?
============


.. admonition:: See

   `SQLite`_



The reason that this application is using a local SQLite file and not a Database that is Server based is, that arma log-files can often contain sensitive or private information.
Either about the server or the user playing on it. Dealing with making a Database Server secure and making sure it does not break any laws, is not something I feel comfortable and also not something I want to do.
Finally I generally dislike the idea of online data collection if it is not absolutely necessary.

SQLite is the best solution for a local Database and has matured a lot in recent years. It is also cross-platform and does not need anything like docker.


ERD
=====

.. image:: /_images/database_graph.png
   :scale: 10 %
   :align: left