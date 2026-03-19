import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import EnhancedTrackList from './EnhancedTrackList'

describe('EnhancedTrackList', ()=>{
  it('renders header', ()=>{
    render(<EnhancedTrackList />)
    expect(screen.getByText(/Sort:/i)).toBeTruthy()
  })
})
