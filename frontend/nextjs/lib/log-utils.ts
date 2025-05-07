import { logsAPI } from './logs-api'

/**
 * Create a log entry in the database
 * 
 * @param message The log message
 * @param level The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
 * @param category The log category
 * @param source The log source
 * @param details Additional details
 * @param entityType The entity type
 * @param entityId The entity ID
 * @returns Promise that resolves when the log is created
 */
export async function createLog(
  message: string,
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' = 'INFO',
  category?: string,
  source?: string,
  details?: any,
  entityType?: string,
  entityId?: string,
): Promise<void> {
  try {
    await logsAPI.createLog({
      message,
      level,
      category,
      source,
      details,
      entity_type: entityType,
      entity_id: entityId,
    })
    console.log(`Log created: [${level}] ${message}`)
  } catch (error) {
    console.error('Error creating log:', error)
  }
}

/**
 * Create a debug log entry
 */
export function logDebug(message: string, category?: string, source?: string, details?: any, entityType?: string, entityId?: string): Promise<void> {
  return createLog(message, 'DEBUG', category, source, details, entityType, entityId)
}

/**
 * Create an info log entry
 */
export function logInfo(message: string, category?: string, source?: string, details?: any, entityType?: string, entityId?: string): Promise<void> {
  return createLog(message, 'INFO', category, source, details, entityType, entityId)
}

/**
 * Create a warning log entry
 */
export function logWarning(message: string, category?: string, source?: string, details?: any, entityType?: string, entityId?: string): Promise<void> {
  return createLog(message, 'WARNING', category, source, details, entityType, entityId)
}

/**
 * Create an error log entry
 */
export function logError(message: string, category?: string, source?: string, details?: any, entityType?: string, entityId?: string): Promise<void> {
  return createLog(message, 'ERROR', category, source, details, entityType, entityId)
}

/**
 * Create a critical log entry
 */
export function logCritical(message: string, category?: string, source?: string, details?: any, entityType?: string, entityId?: string): Promise<void> {
  return createLog(message, 'CRITICAL', category, source, details, entityType, entityId)
}
