#ifndef LIBPQ_FE_H
#define LIBPQ_FE_H

// Mock minimal definitions for libpq to satisfy CMake and libpqxx config
typedef enum { CONNECTION_OK, CONNECTION_BAD } ConnStatusType;
typedef enum { PGRES_COMMAND_OK, PGRES_TUPLES_OK } ExecStatusType;

typedef struct pg_conn PGconn;
typedef struct pg_result PGresult;

#endif
