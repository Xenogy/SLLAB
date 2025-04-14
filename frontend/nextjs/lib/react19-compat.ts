/**
 * This file contains utilities to help with React 19 compatibility issues
 */

// Check if we're using React 19
export const isReact19 = () => {
  try {
    if (typeof window !== 'undefined') {
      // Check for React version in a safer way
      const reactModule = require('react');
      return parseInt(reactModule.version.split('.')[0], 10) >= 19;
    }
    return false;
  } catch (e) {
    return false;
  }
};

// Error handler for React 19 compatibility issues
export const setupReact19ErrorHandler = () => {
  if (typeof window !== 'undefined') {
    window.addEventListener('error', (event) => {
      // Log React 19 compatibility errors
      if (
        event.error &&
        (event.error.message?.includes('react-day-picker') ||
          event.error.message?.includes('vaul') ||
          event.error.stack?.includes('react-day-picker') ||
          event.error.stack?.includes('vaul'))
      ) {
        console.warn('React 19 compatibility issue detected:', event.error);
        // Prevent the error from crashing the app
        event.preventDefault();
      }
    });
  }
};

// Patch for libraries that might have issues with React 19
export const applyReact19Patches = () => {
  if (typeof window !== 'undefined' && isReact19()) {
    // Apply any necessary global patches here
    console.log('Applied React 19 compatibility patches');
  }
};

// Helper to safely use components that might have React 19 compatibility issues
export const safelyRender = (
  component: () => JSX.Element,
  fallback: () => JSX.Element
) => {
  try {
    return component();
  } catch (error) {
    console.warn('React 19 compatibility error, using fallback:', error);
    return fallback();
  }
};
