-- This is a simple pass-through query.
-- It selects all data from the input and sends it to the output.
SELECT
    *
INTO
    [cosmosdb-output]
FROM
    [iothub-input]