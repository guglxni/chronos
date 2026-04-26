/**
 * Text that auto-reveals its full value in a Tooltip if it's truncated.
 *
 * Measures the DOM node after mount (and on resize) to decide whether the
 * text actually overflows — so the tooltip doesn't fire for values that
 * render in full, which would just be noise.
 */
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import Tooltip from './Tooltip';

interface TruncatedTextProps {
  text: string;
  className?: string;
  /** Element tag to render — defaults to <span>. Use <p> for block contexts. */
  as?: 'span' | 'p';
}

export default function TruncatedText({
  text,
  className,
  as = 'span',
}: TruncatedTextProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [isTruncated, setIsTruncated] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const check = () => {
      // scrollWidth > clientWidth means the text is being clipped by overflow:hidden
      setIsTruncated(el.scrollWidth > el.clientWidth + 1);
    };

    check();
    const resizeObserver = new ResizeObserver(check);
    resizeObserver.observe(el);
    return () => resizeObserver.disconnect();
  }, [text]);

  const Tag = as as 'span' | 'p';

  const node = (
    <Tag
      ref={ref as React.Ref<HTMLSpanElement & HTMLParagraphElement>}
      className={clsx('truncate block', className)}
    >
      {text}
    </Tag>
  );

  return (
    <Tooltip content={text} disabled={!isTruncated} placement="top">
      {node}
    </Tooltip>
  );
}
