con <- idaConnect("BLUDB","","")
idaInit(con)
df <- idaShowTables()
schemas <- idaQuery("Select SCHEMANAME from syscat.schemata group by SCHEMANAME")
print(paste('"',schemas$SCHEMANAME,'"',sep='',collapse=','))
idaClose(con)