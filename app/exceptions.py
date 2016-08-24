class Error(Exception):
    """This is the base class of exceptions thrown by this app. 
    """
    def __init__(self, msg):
        """This is the constructor which take one string argument."""
        self.msg = msg
    def __str__(self):
        return('ml-service::'+str(self.__class__.__name__)+': '+str(self.msg))

class UserNotExistsError(Error):
    """
    Exception raised for errors when try to retrieve a user with given name from Cloudant
    but Cloudant returns an empty list.
    """
    def __init__(self, username, msg):
        super(UserNotExistsError, self).__init__(msg)
        self.username = username

class ModelCreationError(Error):
    """Exception raised for errors when try to create a model in corresponding service instance."""
    pass

class ModelRefreshError(Error):
    """Exception raised for errors when try to refresh a model."""
    pass

class RetrieveMetadataError(Error):
    """Exception raised for errors when try to retrieve metadata from service instance."""
    pass

class ModelScoreError(Error):
    """An exception raised when try to score in corresponding service instance."""
    pass

class ModelDeleteError(Error):
    """An exception raised when try to delete a model in corresponding service instance."""
    pass

class ModelVisualizeError(Error):
    """An exception raised when try to visualize a model in corresponding service instance."""
    pass

class ModelAlreadyExistsError(Error):
    """
    Exception raised for errors when try to create a model with given name 
    but that name is already used by existing model.
    """
    def __init__(self, conflict_name, msg):
        super(ModelAlreadyExistsError, self).__init__(msg)
        self.conflict_name = conflict_name

class ModelNotExistsError(Error):
    """
    Exception raised for errors when try to retrieve a model with given name from Cloudant
    but Cloudant returns an empty list.
    """
    def __init__(self, model_name, msg):
        super(ModelNotExistsError, self).__init__(msg)
        self.model_name = model_name

class UnknownDatabaseError(Error):
    """Exception raised for errors when try to interact with database."""
    pass

class DatabaseInitializeError(Error):
    """
    Exception raised for errors when try to initialize database.

    The initialization process include creating 
    'user', 'ml_service', 'ml_service_data' 
    databases in Cloudant instance.
    """
    pass

class DatabaseConnectError(Error):
    """Exception raised for errors when try to connect to Cloudant."""
    pass

class DatabaseDeleteError(Error):
    """Exception raised for errors when try to delete a database in Cloudant."""
    pass

class DatabaseCreateError(Error):
    """Exception raised for errors when try to create a database in Cloudant."""
    pass

class IndexCreateError(Error):
    """Exception raised for errors when try to create indexes for a database in Cloudant."""
    pass

class UnknownDashdbError(Error):
    """Exception raised for errors when try to run R script or SQL on Dashdb instance"""
    pass

class UnknownCloudFoundryError(Error):
    """Exception raised for errors when try to run R script or SQL on Dashdb instance"""
    pass

class UnknownSPSSError(Error):
    """Exception raised for errors when try to interact with SPSS instance"""
    pass

class OperationNotSupportError(Error):
    """Exception raised for errors when try to interact with SPSS instance"""
    pass