con <- idaConnect("BLUDB","","")
idaInit(con)
columns <- paste("'",names(ida.data.frame('<table_name>')),"'",sep='',collapse=",")
cat(paste("{'columns':[",columns,"]}",sep=''))
idaClose(con)

