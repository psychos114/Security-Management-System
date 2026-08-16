import http from './http'


export async function analyzeInspectionImage(
  imageFile,
) {
  const formData = new FormData()

  formData.append(
    'image',
    imageFile,
  )

  const response = await http.post(
    '/api/inspection-vision/analyze',
    formData,
  )

  return response.data
}