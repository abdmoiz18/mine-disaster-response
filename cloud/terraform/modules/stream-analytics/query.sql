/*
Here are links to help you get started with Stream Analytics Query Language:
- Common query patterns - https://go.microsoft.com/fwLink/?LinkID=619153
- Query language - https://docs.microsoft.com/stream-analytics-query/query-language-elements-azure-stream-analytics
*/
-- Main query for miner data processing from IoT Hub to Cosmos DB
-- First query for miner data
-- Combined query for both miner data and gateway status
-- Use json_stringify for complex objects so Cosmos stores the JSON string properly,
-- make battery FLOAT, and use the device timestamp in the id to avoid collisions.
SELECT 
    miner.device_id,
    CONCAT(miner.device_id, '-', REPLACE(CAST(miner.device_timestamp AS NVARCHAR(MAX)), ':', '_')) AS id,
    System.Timestamp() AS processed_time,
    miner.device_timestamp AS device_timestamp,
    json_stringify(miner.ble_readings) AS ble_readings,
    json_stringify(miner.imu_data) AS imu_data,
    CAST(miner.battery AS FLOAT) AS battery,
    CAST(miner.position.x AS FLOAT) AS location_x,
    CAST(miner.position.y AS FLOAT) AS location_y,
    'simulator' AS source_device,
    'miner_telemetry' AS message_type
INTO
    [miner-telemetry]
FROM
    [proto-mine-resp] miner
WHERE
    miner.device_id LIKE 'miner_%'

UNION ALL

SELECT
    gateway.gateway_id AS device_id,
    CONCAT(gateway.gateway_id, '-', REPLACE(CAST(gateway.timestamp AS NVARCHAR(MAX)), ':', '_')) AS id,
    System.Timestamp() AS processed_time,
    gateway.timestamp AS device_timestamp,
    NULL AS ble_readings,
    NULL AS imu_data,
    CAST(NULL AS FLOAT) AS battery,
    CAST(NULL AS FLOAT) AS location_x,
    CAST(NULL AS FLOAT) AS location_y,
    'simulator' AS source_device,
    'gateway_status' AS message_type
FROM
    [proto-mine-resp] gateway
WHERE
    gateway.gateway_id IS NOT NULL;