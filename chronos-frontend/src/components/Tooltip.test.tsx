import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react';
import Tooltip from './Tooltip';

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('Tooltip', () => {
  it('renders the trigger child without the tooltip content initially', () => {
    render(
      <Tooltip content="hello world">
        <button type="button">Trigger</button>
      </Tooltip>,
    );
    expect(screen.getByText('Trigger')).toBeInTheDocument();
    expect(screen.queryByText('hello world')).not.toBeInTheDocument();
  });

  it('shows the tooltip on focus', async () => {
    render(
      <Tooltip content="focus-visible tip" openDelay={0}>
        <button type="button">Focus me</button>
      </Tooltip>,
    );

    const btn = screen.getByText('Focus me');
    fireEvent.focus(btn);

    await waitFor(() => {
      expect(screen.getByText('focus-visible tip')).toBeInTheDocument();
    });
  });

  it('does not render when disabled', async () => {
    render(
      <Tooltip content="should not show" disabled openDelay={0}>
        <button type="button">Trigger</button>
      </Tooltip>,
    );

    const btn = screen.getByText('Trigger');
    fireEvent.focus(btn);

    // Give floating-ui a tick
    await new Promise((r) => setTimeout(r, 50));
    expect(screen.queryByText('should not show')).not.toBeInTheDocument();
  });
});
