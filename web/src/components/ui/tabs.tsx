import * as TabsPrimitive from '@radix-ui/react-tabs'
import * as React from 'react'

import { cn } from '@/lib/utils'

export function Tabs({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Root>): React.JSX.Element {
  return <TabsPrimitive.Root className={cn('w-full', className)} {...props} />
}

export function TabsList({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>): React.JSX.Element {
  return (
    <TabsPrimitive.List
      className={cn(
        'inline-flex h-auto max-w-full items-center justify-start gap-1 overflow-x-auto rounded-md bg-slate-100 p-1 text-slate-600',
        className,
      )}
      {...props}
    />
  )
}

export function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>): React.JSX.Element {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        'inline-flex min-h-9 shrink-0 items-center justify-center whitespace-nowrap rounded-sm px-3 py-2 text-sm font-medium transition-all focus-visible:outline-none data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm',
        className,
      )}
      {...props}
    />
  )
}

export function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>): React.JSX.Element {
  return <TabsPrimitive.Content className={cn('mt-4', className)} {...props} />
}
