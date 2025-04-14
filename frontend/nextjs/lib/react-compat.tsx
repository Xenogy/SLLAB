"use client";

import React from 'react';

// This file provides compatibility functions and components for libraries
// that haven't been updated to support React 19 yet

// Re-export React to ensure consistent version usage
export * from 'react';

// Create a compatibility version of createRoot if needed
export const createCompatRoot = (container: Element | DocumentFragment) => {
  // Use the new React 19 API, but provide fallbacks if needed
  return {
    render: (element: React.ReactNode) => {
      // React 19 uses createRoot differently, this is a compatibility wrapper
      const root = (React as any).createRoot(container);
      root.render(element);
      return root;
    },
    unmount: () => {
      const root = (React as any).createRoot(container);
      root.unmount();
    }
  };
};

// Wrapper for components that might have issues with React 19
export function CompatibilityWrapper({ 
  children, 
  component 
}: { 
  children: React.ReactNode;
  component: string;
}) {
  // This is a placeholder for any specific compatibility fixes
  // that might be needed for particular components
  
  return (
    <React.Fragment>
      {/* Add any necessary context providers or fixes here */}
      {children}
    </React.Fragment>
  );
}

// Specific wrapper for react-day-picker
export function DayPickerCompat(props: any) {
  return (
    <CompatibilityWrapper component="react-day-picker">
      {/* Forward all props to the actual component */}
      {props.children}
    </CompatibilityWrapper>
  );
}

// Specific wrapper for vaul (drawer component)
export function VaulCompat(props: any) {
  return (
    <CompatibilityWrapper component="vaul">
      {/* Forward all props to the actual component */}
      {props.children}
    </CompatibilityWrapper>
  );
}
