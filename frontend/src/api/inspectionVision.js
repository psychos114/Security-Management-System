import http from './http'


export async function analyzeInspectionImage(
  imageFile,
  description = '',
) {
  const formData = new FormData()

  formData.append(
    'image',
    imageFile,
  )

  if (description.trim()) {
    formData.append(
      'description',
      description.trim(),
    )
  }

  const response = await http.post(
    '/api/inspection-vision/analyze',
    formData,
  )

  return response.data
}
