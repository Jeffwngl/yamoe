// chatgpt was used to assist in writing this code, I don't know much swift lol

import AppKit
import VisionKit
import ImageIO
import Foundation
import Darwin

struct OCRRequest: Decodable {
    let image: String
    let language: String
}

struct OCRResponse: Encodable {
    let text: String
    let error: String?
}

@main
struct VisionKitHelper {
    static func respond(_ result: OCRResponse) {
        guard let data = try? JSONEncoder().encode(result),
              let line = String(data: data, encoding: .utf8)
        else {
            return
        }

        print(line)
        fflush(stdout)
    }

    static func main() async {
        guard ImageAnalyzer.isSupported else {
            fputs("VisionKit ImageAnalyzer is unsupported\n", stderr)
            return
        }

        // reuse the analyzer across requests
        let analyzer = ImageAnalyzer()

        while let line = readLine() {
            do {
                let request = try JSONDecoder().decode(
                    OCRRequest.self,
                    from: Data(line.utf8)
                )

                guard let imageData = Data(
                    base64Encoded: request.image
                ),
                let image = NSImage(data: imageData)
                else {
                    respond(OCRResponse(
                        text: "",
                        error: "Invalid image data"
                    ))
                    continue
                }

                var config = ImageAnalyzer.Configuration([.text])
                config.locales = [request.language]

                let analysis = try await analyzer.analyze(
                    image,
                    orientation: .up,
                    configuration: config
                )

                let text = analysis.hasResults(for: .text)
                    ? analysis.transcript
                    : ""

                respond(OCRResponse(
                    text: text,
                    error: nil
                ))
            } catch {
                respond(OCRResponse(
                    text: "",
                    error: String(describing: error)
                ))
            }
        }
    }
}
