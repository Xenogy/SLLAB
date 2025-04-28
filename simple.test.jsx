import React from 'react';
import { render, screen } from '@testing-library/react';

// A simple component to test
const SimpleComponent = () => {
  return <div>Hello, World!</div>;
};

describe('SimpleComponent', () => {
  it('renders the component', () => {
    render(<SimpleComponent />);
    expect(screen.getByText('Hello, World!')).toBeInTheDocument();
  });
});
