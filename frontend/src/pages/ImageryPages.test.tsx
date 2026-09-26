// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../services/api'
import { SatellitePage } from './SatellitePage'
import { SonarPage } from './SonarPage'

vi.mock('../services/api', () => ({ api: {
  satelliteStatus: vi.fn(), satelliteUpload: vi.fn(), satelliteAnalyze: vi.fn(), satelliteAsset: vi.fn(() => '/demo.png'),
  sonarReplay: vi.fn(), sonarStatus: vi.fn(), sonarUpload: vi.fn(), sonarAnalyze: vi.fn(), sonarAsset: vi.fn(() => '/upload.png'),
}, errorMessage: (e: unknown) => String(e) }))

function page(element: React.ReactNode) {
  return render(<MemoryRouter initialEntries={['/missions/7/view']}><Routes><Route path="/missions/:id/view" element={element} /></Routes></MemoryRouter>)
}

beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.satelliteStatus).mockResolvedValue({ demo_available: true, uploaded_before: false, uploaded_after: false, classical_cv_available: true, ml_model_configured: false }); vi.mocked(api.sonarStatus).mockResolvedValue({ uploaded_frame: false, ml_model_configured: false }) })
afterEach(cleanup)

describe('satellite page', () => {
  it('runs bundled change analysis and displays mask and regions', async () => {
    vi.mocked(api.satelliteAnalyze).mockResolvedValue({ detector: 'CLASSICAL_CV_BASELINE', source_type: 'SIMULATED_DEMO_DATA', changed_pixels: 120, percent_changed: 1.5, regions: [{ x: 2, y: 3, width: 8, height: 9 }], mask_data_url: 'data:image/png;base64,abc', width: 100, height: 80 })
    page(<SatellitePage />)
    await screen.findByText('Image source')
    fireEvent.click(screen.getByRole('button', { name: 'Run Analysis' }))
    expect(await screen.findByText('1.5%')).toBeTruthy()
    expect(screen.getByAltText('Binary change mask')).toBeTruthy()
    expect(api.satelliteAnalyze).toHaveBeenCalledWith(7, 'demo')
  })
  it('uploads a before image and switches to uploaded source', async () => {
    vi.mocked(api.satelliteUpload).mockResolvedValue({})
    page(<SatellitePage />)
    const file = new File(['image'], 'before.png', { type: 'image/png' })
    fireEvent.change(await screen.findByLabelText('Upload before'), { target: { files: [file] } })
    await waitFor(() => expect(api.satelliteUpload).toHaveBeenCalledWith(7, 'before', file))
    expect((screen.getByRole('radio', { name: 'My uploads' }) as HTMLInputElement).checked).toBe(true)
  })
})

describe('sonar page', () => {
  it('replays bundled frames and analyzes uploaded image', async () => {
    vi.mocked(api.sonarReplay).mockResolvedValue({ source_type: 'SIMULATED_DEMO_DATA', detector: 'DEMO_ANNOTATIONS', frames: [1, 2].map(n => ({ name: `frame-${n}.png`, frame_number: n, width: 100, height: 80, image_url: `/frame-${n}.png`, metadata: { scenario: 'Fictional replay', sample_index: n }, annotations: [{ x: 10, y: 10, width: 20, height: 20, label: 'Synthetic echo annotation', source_type: 'DEMO_ANNOTATION' }] })) })
    vi.mocked(api.sonarUpload).mockResolvedValue({})
    vi.mocked(api.sonarAnalyze).mockResolvedValue({ detector: 'HEURISTIC_ANOMALY_BASELINE', source_type: 'USER_UPLOAD', output_source: 'HEURISTIC', anomaly_count: 1, anomaly_score: 0.7, width: 100, height: 80, regions: [{ x: 20, y: 20, width: 10, height: 10, label: 'Unknown anomaly', score: 0.7 }] })
    page(<SonarPage />)
    expect(await screen.findByText(/Frame 1 of 2/)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText(/Frame 2 of 2/)).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Upload sonar image'), { target: { files: [new File(['image'], 'sonar.png', { type: 'image/png' })] } })
    await waitFor(() => expect(api.sonarUpload).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: 'Run heuristic analysis' }))
    expect(await screen.findByText(/1 unknown anomaly regions/)).toBeTruthy()
  })
})
