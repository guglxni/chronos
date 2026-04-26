/**
 * Floating UI tooltip for CHRONOS.
 *
 * Wraps any trigger child and shows a dark surface on hover / focus.  Positions
 * itself automatically (offset + flip + shift + arrow) and uses ARIA so screen
 * readers announce the content.  Keyboard-accessible via focus events.
 */
import { cloneElement, isValidElement, useRef, useState } from 'react';
import type { ReactElement, ReactNode } from 'react';
import {
  useFloating,
  useHover,
  useFocus,
  useDismiss,
  useRole,
  useInteractions,
  offset,
  flip,
  shift,
  arrow,
  FloatingArrow,
  FloatingPortal,
  autoUpdate,
  safePolygon,
} from '@floating-ui/react';
import type { Placement } from '@floating-ui/react';

interface TooltipProps {
  content: ReactNode;
  children: ReactElement;
  placement?: Placement;
  /** Delay in ms before the tooltip opens on hover. Default 150. */
  openDelay?: number;
  /** Disable rendering — useful when the trigger content isn't truncated. */
  disabled?: boolean;
}

export default function Tooltip({
  content,
  children,
  placement = 'top',
  openDelay = 150,
  disabled = false,
}: TooltipProps) {
  const [open, setOpen] = useState(false);
  const arrowRef = useRef<SVGSVGElement | null>(null);

  const { refs, floatingStyles, context } = useFloating({
    open,
    onOpenChange: setOpen,
    placement,
    middleware: [offset(8), flip(), shift({ padding: 8 }), arrow({ element: arrowRef })],
    whileElementsMounted: autoUpdate,
  });

  const hover = useHover(context, {
    delay: { open: openDelay, close: 0 },
    handleClose: safePolygon(),
    enabled: !disabled,
  });
  const focus = useFocus(context, { enabled: !disabled });
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'tooltip' });

  const { getReferenceProps, getFloatingProps } = useInteractions([
    hover,
    focus,
    dismiss,
    role,
  ]);

  if (!isValidElement(children)) return children;

  // Passing ref + handlers through to the trigger element.  Using cloneElement
  // keeps the original component's DOM intact so semantics don't change.
  const triggerProps = getReferenceProps({
    ref: refs.setReference,
    ...(children.props as Record<string, unknown>),
  }) as Record<string, unknown>;

  return (
    <>
      {cloneElement(children, triggerProps)}
      {open && !disabled && (
        <FloatingPortal>
          <div
            ref={refs.setFloating}
            style={floatingStyles}
            className="floating-tooltip"
            {...getFloatingProps()}
          >
            {content}
            <FloatingArrow
              ref={arrowRef}
              context={context}
              fill="#111827"
              stroke="#374151"
              strokeWidth={1}
            />
          </div>
        </FloatingPortal>
      )}
    </>
  );
}
