library(ibmdbR)
mycon <- idaConnect("BLUDB", "", "")
idaInit(mycon)
df <- data.frame(tables=c(<table_names>))
for (table in df$tables) { idaDeleteTable(table) }
cat("{'message':'OK'}")
idaClose(mycon)

# library(ibmdbR)
# mycon <- idaConnect("BLUDB", "", "")
# idaInit(mycon)
# df <- data.frame(tables=c('RENAME_TEST', 'RENAME_TEST1'))
# for (table in df$tables) { idaDeleteTable(table) }
# cat("{'message':'OK'}")
# idaClose(mycon)
