import Foundation

#if os(macOS)
import FoundationModels
#endif

enum FoundationModelsTool {

    static func query(payload: [String: Any]) async throws -> Any {
        guard let prompt = payload.string("prompt"), !prompt.isEmpty else {
            throw CLIError("Missing required argument: prompt")
        }
        let systemPrompt = payload.string("system") ?? "You are a helpful assistant. Be concise and direct."
        let maxTokens = payload.int("max_tokens") ?? 256

        if #available(macOS 26.0, *) {
            let response = try await callNativeFoundationModels(prompt: prompt, system: systemPrompt, maxTokens: maxTokens)
            if !response.isEmpty { return response }
        }

        let response = try await callLocalLLMServer(prompt: prompt, system: systemPrompt, maxTokens: maxTokens)
        if response.isEmpty { return "Foundation Models returned no output." }
        return response
    }

    @available(macOS 26.0, *)
    private static func callNativeFoundationModels(prompt: String, system: String, maxTokens: Int) async throws -> String {
        let session = LanguageModelSession()
        let fullPrompt = "System: \(system)\n\nUser: \(prompt)"
        let response = try await session.respond(to: fullPrompt)
        return response.content
    }

    private static func callLocalLLMServer(prompt: String, system: String, maxTokens: Int) async throws -> String {
        let endpoint = "http://localhost:8000/api/generate"
        guard let url = URL(string: endpoint) else {
            throw CLIError("Invalid endpoint URL")
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "prompt": prompt, "system": system, "max_tokens": maxTokens, "temperature": 0.3
        ])
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            return "*(Foundation Models LLM unavailable — macOS < 26.0 and no local server on \(endpoint))*"
        }
        if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
           let result = json["result"] as? String { return result }
        return ""
    }
}
