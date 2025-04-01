"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function SearchForm() {
  const [query, setQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const router = useRouter()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsSearching(true)

    // In a real app, this would update the URL with the search query
    // and trigger a server fetch for product data
    router.push(`/?q=${encodeURIComponent(query)}`)

    // Simulate search delay
    setTimeout(() => {
      setIsSearching(false)
      // The ProductResults component would handle displaying results
      // based on the URL query parameter
    }, 800)
  }

  return (
    <form onSubmit={handleSearch} className="mx-auto max-w-2xl">
      <div className="flex w-full items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
          <Input
            type="text"
            placeholder="Search for products (e.g., iPhone 15, Samsung TV, Headphones)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button type="submit" disabled={isSearching}>
          {isSearching ? "Searching..." : "Compare Prices"}
        </Button>
      </div>
    </form>
  )
}

