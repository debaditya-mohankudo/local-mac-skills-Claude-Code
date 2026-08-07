import Foundation
import CoreAudio

enum SoundTool {

    // MARK: - List devices

    static func listDevices(payload: [String: Any]) async throws -> Any {
        let filter = payload.string("type") ?? "output"  // "output", "input", or "all"
        let devices = try getAudioDevices()
        let filtered = devices.filter { d in
            switch filter {
            case "input":  return d.isInput
            case "output": return d.isOutput
            default:       return true
            }
        }
        let current = try? getDefaultOutputDevice()
        return filtered.map { d -> [String: Any] in
            [
                "id":        d.id,
                "name":      d.name,
                "is_input":  d.isInput,
                "is_output": d.isOutput,
                "is_default_output": d.name == current?.name
            ]
        }
    }

    // MARK: - Get current output

    static func getOutput(payload: [String: Any]) async throws -> Any {
        guard let device = try? getDefaultOutputDevice() else {
            return ["error": "Could not read default output device"]
        }
        return ["device": device.name, "id": device.id]
    }

    // MARK: - Set output device

    static func setOutput(payload: [String: Any]) async throws -> Any {
        guard let name = payload.string("name") else {
            throw CLIError("Missing required argument: name")
        }
        let devices = try getAudioDevices()
        guard let target = devices.first(where: {
            $0.isOutput && $0.name.lowercased().contains(name.lowercased())
        }) else {
            let available = devices.filter(\.isOutput).map(\.name).joined(separator: ", ")
            throw CLIError("No output device matching '\(name)'. Available: \(available)")
        }
        try setDefaultOutputDevice(id: target.id)
        return ["ok": true, "device": target.name]
    }

    // MARK: - Get / Set system volume

    static func getVolume(payload: [String: Any]) async throws -> Any {
        let vol = try getSystemVolume()
        let muted = try getSystemMute()
        return ["volume": Int(vol * 100), "muted": muted]
    }

    static func setVolume(payload: [String: Any]) async throws -> Any {
        guard let level = payload["level"] as? Int ?? (payload["level"] as? Double).map(Int.init) else {
            throw CLIError("Missing required argument: level (0–100)")
        }
        guard level >= 0 && level <= 100 else {
            throw CLIError("level must be between 0 and 100")
        }
        let scalar = Float(level) / 100.0
        try setSystemVolume(scalar)
        return ["ok": true, "volume": level]
    }

    // MARK: - Mute / Unmute

    static func mute(payload: [String: Any]) async throws -> Any {
        try setSystemMute(true)
        return ["ok": true, "muted": true]
    }

    static func unmute(payload: [String: Any]) async throws -> Any {
        try setSystemMute(false)
        return ["ok": true, "muted": false]
    }

    // MARK: - CoreAudio helpers

    private struct AudioDevice {
        let id: AudioDeviceID
        let name: String
        let isInput: Bool
        let isOutput: Bool
    }

    private static func getAudioDevices() throws -> [AudioDevice] {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDevices,
            mScope:    kAudioObjectPropertyScopeGlobal,
            mElement:  kAudioObjectPropertyElementMain
        )
        var dataSize: UInt32 = 0
        var status = AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &propAddr, 0, nil, &dataSize)
        guard status == noErr else { throw CLIError("CoreAudio: failed to get device list size (\(status))") }

        let count = Int(dataSize) / MemoryLayout<AudioDeviceID>.size
        var deviceIDs = [AudioDeviceID](repeating: 0, count: count)
        status = AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &propAddr, 0, nil, &dataSize, &deviceIDs)
        guard status == noErr else { throw CLIError("CoreAudio: failed to get device IDs (\(status))") }

        return deviceIDs.compactMap { id -> AudioDevice? in
            guard let name = deviceName(id: id) else { return nil }
            return AudioDevice(
                id:       id,
                name:     name,
                isInput:  hasChannels(id: id, scope: kAudioDevicePropertyScopeInput),
                isOutput: hasChannels(id: id, scope: kAudioDevicePropertyScopeOutput)
            )
        }
    }

    private static func deviceName(id: AudioDeviceID) -> String? {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyDeviceNameCFString,
            mScope:    kAudioObjectPropertyScopeGlobal,
            mElement:  kAudioObjectPropertyElementMain
        )
        var name: CFString = "" as CFString
        var dataSize = UInt32(MemoryLayout<CFString>.size)
        let status = AudioObjectGetPropertyData(id, &propAddr, 0, nil, &dataSize, &name)
        guard status == noErr else { return nil }
        return name as String
    }

    private static func hasChannels(id: AudioDeviceID, scope: AudioObjectPropertyScope) -> Bool {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyStreamConfiguration,
            mScope:    scope,
            mElement:  kAudioObjectPropertyElementMain
        )
        var dataSize: UInt32 = 0
        guard AudioObjectGetPropertyDataSize(id, &propAddr, 0, nil, &dataSize) == noErr,
              dataSize > 0 else { return false }
        let bufferList = UnsafeMutablePointer<AudioBufferList>.allocate(capacity: Int(dataSize))
        defer { bufferList.deallocate() }
        guard AudioObjectGetPropertyData(id, &propAddr, 0, nil, &dataSize, bufferList) == noErr else { return false }
        return bufferList.pointee.mNumberBuffers > 0
    }

    private static func getDefaultOutputDevice() throws -> AudioDevice {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDefaultOutputDevice,
            mScope:    kAudioObjectPropertyScopeGlobal,
            mElement:  kAudioObjectPropertyElementMain
        )
        var deviceID: AudioDeviceID = kAudioDeviceUnknown
        var dataSize = UInt32(MemoryLayout<AudioDeviceID>.size)
        let status = AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &propAddr, 0, nil, &dataSize, &deviceID)
        guard status == noErr, deviceID != kAudioDeviceUnknown else {
            throw CLIError("CoreAudio: could not get default output device")
        }
        let name = deviceName(id: deviceID) ?? "Unknown"
        return AudioDevice(id: deviceID, name: name, isInput: false, isOutput: true)
    }

    private static func setDefaultOutputDevice(id: AudioDeviceID) throws {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioHardwarePropertyDefaultOutputDevice,
            mScope:    kAudioObjectPropertyScopeGlobal,
            mElement:  kAudioObjectPropertyElementMain
        )
        var deviceID = id
        let dataSize = UInt32(MemoryLayout<AudioDeviceID>.size)
        let status = AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &propAddr, 0, nil, dataSize, &deviceID)
        guard status == noErr else {
            throw CLIError("CoreAudio: failed to set default output device (\(status))")
        }
    }

    private static func getSystemVolume() throws -> Float {
        let defaultDevice = try getDefaultOutputDevice()
        // Try master volume scalar first, then per-channel average
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVolumeScalar,
            mScope:    kAudioDevicePropertyScopeOutput,
            mElement:  kAudioObjectPropertyElementMain
        )
        var volume: Float = 0
        var dataSize = UInt32(MemoryLayout<Float>.size)
        if AudioObjectGetPropertyData(defaultDevice.id, &propAddr, 0, nil, &dataSize, &volume) == noErr {
            return volume
        }
        // Fallback: average channel 1 and 2
        var ch1: Float = 0; var ch2: Float = 0
        propAddr.mElement = 1
        AudioObjectGetPropertyData(defaultDevice.id, &propAddr, 0, nil, &dataSize, &ch1)
        propAddr.mElement = 2
        AudioObjectGetPropertyData(defaultDevice.id, &propAddr, 0, nil, &dataSize, &ch2)
        return (ch1 + ch2) / 2.0
    }

    private static func setSystemVolume(_ volume: Float) throws {
        let defaultDevice = try getDefaultOutputDevice()
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyVolumeScalar,
            mScope:    kAudioDevicePropertyScopeOutput,
            mElement:  kAudioObjectPropertyElementMain
        )
        var vol = volume
        let dataSize = UInt32(MemoryLayout<Float>.size)
        // Try master channel first
        if AudioObjectSetPropertyData(defaultDevice.id, &propAddr, 0, nil, dataSize, &vol) == noErr { return }
        // Fallback: set channels 1 and 2
        propAddr.mElement = 1
        AudioObjectSetPropertyData(defaultDevice.id, &propAddr, 0, nil, dataSize, &vol)
        propAddr.mElement = 2
        let status = AudioObjectSetPropertyData(defaultDevice.id, &propAddr, 0, nil, dataSize, &vol)
        guard status == noErr else { throw CLIError("CoreAudio: failed to set volume (\(status))") }
    }

    private static func getSystemMute() throws -> Bool {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyMute,
            mScope:    kAudioDevicePropertyScopeOutput,
            mElement:  kAudioObjectPropertyElementMain
        )
        let defaultDevice = try getDefaultOutputDevice()
        var muted: UInt32 = 0
        var dataSize = UInt32(MemoryLayout<UInt32>.size)
        let status = AudioObjectGetPropertyData(defaultDevice.id, &propAddr, 0, nil, &dataSize, &muted)
        guard status == noErr else { throw CLIError("CoreAudio: failed to get mute state (\(status))") }
        return muted != 0
    }

    private static func setSystemMute(_ mute: Bool) throws {
        var propAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyMute,
            mScope:    kAudioDevicePropertyScopeOutput,
            mElement:  kAudioObjectPropertyElementMain
        )
        let defaultDevice = try getDefaultOutputDevice()
        var muted: UInt32 = mute ? 1 : 0
        let dataSize = UInt32(MemoryLayout<UInt32>.size)
        let status = AudioObjectSetPropertyData(defaultDevice.id, &propAddr, 0, nil, dataSize, &muted)
        guard status == noErr else { throw CLIError("CoreAudio: failed to set mute (\(status))") }
    }
}
