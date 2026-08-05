import duckdb
con = duckdb.connect("./storage/alpha_node.duckdb", read_only=True)
print(con.execute("DESCRIBE nq_1m;").fetchdf())
con.close()