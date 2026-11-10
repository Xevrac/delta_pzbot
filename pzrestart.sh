#!/usr/bin/env bash
SERVER_HOST="${PZ_HOST:?PZ_HOST is not set}"
RCON_PORT="${RCON_PORT:?RCON_PORT is not set}"
RCON_PASSWORD="${RCON_PASSWORD:?RCON_PASSWORD is not set}"
PZ="$(dirname "$0")/pz.py"

echo "Starting auto-restart sequence..."

echo "System core error. Restart sequence engaged. T-2 minutes."
python3 "$PZ" "$SERVER_HOST" "$RCON_PORT" "$RCON_PASSWORD" 'servermsg "System core error. Restart sequence engaged. T-2 minutes."'
sleep 60

echo "No viable alternative detected. Emergency purge protocol armed. T-1 minute."
python3 "$PZ" "$SERVER_HOST" "$RCON_PORT" "$RCON_PASSWORD" 'servermsg "No viable alternative detected. Emergency purge protocol armed. T-1 minute."'
sleep 60

echo "PREPARING FOR PURGE"
python3 "$PZ" "$SERVER_HOST" "$RCON_PORT" "$RCON_PASSWORD" 'servermsg "PREPARING FOR PURGE"'
sleep 10

echo "Sending final server quit command..."
python3 "$PZ" "$SERVER_HOST" "$RCON_PORT" "$RCON_PASSWORD" quit

echo "Auto-restart sequence complete."