"use client"

import { useEffect } from "react"
import { setupReact19ErrorHandler, applyReact19Patches } from "@/lib/react19-compat"

export function ReactCompatInitializer() {
  // Initialize React 19 compatibility layer
  useEffect(() => {
    // Set up global error handler for React 19 compatibility issues
    setupReact19ErrorHandler();
    
    // Apply any necessary patches for React 19 compatibility
    applyReact19Patches();
    
    console.log('React 19 compatibility layer initialized');
  }, []);
  
  return null; // This component doesn't render anything
}
