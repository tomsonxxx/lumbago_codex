import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LibraryBrowser from '../LibraryBrowser'

describe('LibraryBrowser', () => {
  it('shows title', () => {
    render(<LibraryBrowser />)
    expect(screen.getByText(/Library/i)).toBeTruthy()
  })
})
