"use client";

import * as React from "react";
import { format } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import { DayPicker } from "react-day-picker";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DayPickerCompat } from "@/lib/react-compat";

export type DatePickerProps = {
  date?: Date;
  setDate?: (date?: Date) => void;
  disabled?: boolean;
  className?: string;
};

export function DatePicker({ date, setDate, disabled, className }: DatePickerProps) {
  // Use a ref to detect any React 19 specific errors
  const dayPickerRef = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState<boolean>(false);

  // Error handling for React 19 compatibility issues
  React.useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      // Check if the error is related to our date picker
      if (
        dayPickerRef.current && 
        event.error && 
        (event.error.message?.includes('react-day-picker') || 
         event.error.stack?.includes('react-day-picker'))
      ) {
        setError(true);
        console.warn('React 19 compatibility issue with react-day-picker:', event.error);
      }
    };

    window.addEventListener('error', handleError as any);
    return () => window.removeEventListener('error', handleError as any);
  }, []);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-full justify-start text-left font-normal",
            !date && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, "PPP") : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div ref={dayPickerRef}>
          {error ? (
            <div className="p-4 text-sm text-red-500">
              There was an issue loading the date picker with React 19.
              Please try again or select a date manually.
            </div>
          ) : (
            <DayPickerCompat>
              <DayPicker
                mode="single"
                selected={date}
                onSelect={setDate}
                initialFocus
                className="p-3"
              />
            </DayPickerCompat>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
