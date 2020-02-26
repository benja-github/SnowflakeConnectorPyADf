__validBlobFolderNameRegex = @"^[A-Za-z0-9_-]+$";
# The parameter name corresponds to a restricted Snowflake unquoted identifier
# https://docs.snowflake.net/manuals/sql-reference/identifiers-syntax.html
__validParameterNameRegex = @"^[A-Za-z_]{1}[A-Za-z0-9_-]*$";
# This is pretty restrictive
__validParameterTypeRegex = @"^VARCHAR|NUMBER$";
__validParameterValueRegex = @"^[A-Za-z0-9./\\ :_-]+$";


