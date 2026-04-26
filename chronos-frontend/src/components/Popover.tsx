/**
 * Floating UI popover for click/tap-triggered overlays.
 *
 * Used by CHRONOS for the "show all owners" and action-menu cases where a
 * tooltip is not enough — we need the surface to stay open, receive focus,
 * and support clicking links inside.
 */
import { cloneElement, isValidElement, useRef, useState } from 'react';
import type { ReactElement, ReactNode } from 'react';
import {
  useFloating,
  useClick,
  useDismiss,
  useRole,
  useInteractions,
  offset,
  flip,
  shift,
  arrow,
  FloatingArrow,
  FloatingFocusManager,
  FloatingPortal,
  autoUpdate,
} from '@floating-ui/react';
import type { Placement } from '@floating-ui/react';

interface PopoverProps {
  children: ReactElement;
  content: ReactNode | ((close: () => void) => ReactNode);
  placement?: Placement;
  /** Default false — we open on click. Pass true for "always open" (for testing). */
  defaultOpen?: boolean;
}

export default function Popover({
  children,
  content,
  placement = 'bottom-start',
  defaultOpen = false,
}: PopoverProps) {
  const [open, setOpen] = useState(defaultOpen);
  const arrowRef = useRef<SVGSVGElement | null>(null);

  const { refs, floatingStyles, context } = useFloating({
    open,
    onOpenChange: setOpen,
    placement,
    middleware: [offset(8), flip(), shift({ padding: 8 }), arrow({ element: arrowRef })],
    whileElementsMounted: autoUpdate,
  });

  const click = useClick(context);
  const dismiss = useDismiss(context, { outsidePress: true, escapeKey: true });
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([
    click,
    dismiss,
    role,
  ]);

  if (!isValidElement(children)) return children;

  const triggerProps = getReferenceProps({
    ref: refs.setReference,
    ...(children.props as Record<string, unknown>),
  }) as Record<string, unknown>;

  const close = () => setOpen(false);
  const resolved = typeof content === 'function' ? content(close) : content;

  return (
    <>
      {cloneElement(children, triggerProps)}
      {open && (
        <FloatingPortal>
          <FloatingFocusManager context={context} modal={false}>
            <div
              ref={refs.setFloating}
              style={floatingStyles}
              className="bg-gray-900 text-gray-100 text-sm rounded-lg shadow-2xl border border-gray-700 z-50 min-w-[200px] max-w-sm p-3"
              {...getFloatingProps()}
            >
              {resolved}
              <FloatingArrow
                ref={arrowRef}
                context={context}
                fill="#111827"
                stroke="#374151"
                strokeWidth={1}
              />
            </div>
          </FloatingFocusManager>
        </FloatingPortal>
      )}
    </>
  );
}
