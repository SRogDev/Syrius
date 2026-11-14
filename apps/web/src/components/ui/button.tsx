import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

// shadcn/ui-style button, restyled to the Syrius HUD design system
// (Background #111318, Surface #20242C, Platinum #BFC5CE,
// Highlight #E7EBF2). No `asChild` support in Phase 0 — nothing uses it.

const buttonVariants = cva(
  'inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-none border font-mono text-sm font-medium uppercase tracking-widest transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-highlight disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'border-highlight bg-highlight text-bg hover:border-platinum hover:bg-platinum',
        outline:
          'border-line bg-transparent text-highlight hover:border-platinum hover:text-platinum',
        ghost: 'border-transparent text-platinum hover:text-highlight',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 px-3 text-xs',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = 'Button';

export { Button, buttonVariants };
