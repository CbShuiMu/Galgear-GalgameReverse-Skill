// GalSkill CLI and validation adapter for GalArc, 2026-10-22.
// Distributed under GPL-3.0-or-later; see ../LICENSE.txt and ../NOTICE.txt.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;

internal static class Program {
    private static readonly Encoding Names = Encoding.GetEncoding(932,
        EncoderFallback.ExceptionFallback, DecoderFallback.ExceptionFallback);
    private static readonly byte[] NoaMagic = {
        0x45,0x6e,0x74,0x69,0x73,0x1a,0,0,0,4,0,2,0,0,0,0 };
    private sealed class Entry {
        public string name { get; set; }
        public long offset { get; set; }
        public long size { get; set; }
    }

    private static void Help() {
        Console.WriteLine("GalArc CLI subset 1.0 (GalArc ee1f7cda6123821fe7e5dbe456322a7cd49e95b5)");
        Console.WriteLine("galarc.exe list <ns2|noa> INPUT");
        Console.WriteLine("galarc.exe extract <ns2|noa> INPUT OUTPUT_DIR");
        Console.WriteLine("galarc.exe pack ns2 INPUT_DIR OUTPUT");
        Console.WriteLine("galarc.exe pack noa INPUT_DIR OUTPUT --raw");
        Console.WriteLine("NOA: canonical raw flat archives only; no compression/encryption or metadata preservation.");
        Console.WriteLine("NS2: unencrypted raw members; recursive input. Names: strict CP932.");
        Console.WriteLine("Outputs must not exist. No overwrite, GUI, game execution, or implicit format conversion.");
    }

    public static int Main(string[] args) {
        if (args.Length == 0 || (args.Length == 1 &&
            (args[0] == "--help" || args[0] == "-h" || args[0] == "--version"))) {
            Help(); return 0;
        }
        if (args.Length < 3 || (args[1] != "ns2" && args[1] != "noa") ||
            (args[0] != "list" && args[0] != "extract" && args[0] != "pack") ||
            (args[0] == "list" && args.Length != 3) ||
            (args[0] == "extract" && args.Length != 4) ||
            (args[0] == "pack" && args[1] == "ns2" && args.Length != 4) ||
            (args[0] == "pack" && args[1] == "noa" &&
                (args.Length != 5 || args[4] != "--raw"))) {
            Console.Error.WriteLine("Invalid arguments. Use --help. NOA creation requires --raw."); return 2;
        }
        try {
            Utility.ArcEncoding.Shift_JIS = Names;
            ArcFormats.Config.Encoding = Names;
            string input = CanonicalPath(args[2]);
            if (args[0] == "pack") {
                Pack(args[1], input, CanonicalPath(args[3]));
            } else {
                List<Entry> entries = Read(args[1], input);
                if (args[0] == "list")
                    Console.WriteLine(new JavaScriptSerializer().Serialize(entries));
                else Extract(args[1], input, CanonicalPath(args[3]), entries);
            }
            return 0;
        } catch (Exception ex) {
            Console.Error.WriteLine("Error: " + ex.Message); return 1;
        }
    }

    private static void Require(bool valid, string message) {
        if (!valid) throw new InvalidDataException(message);
    }
    private static string Prefix(string path) {
        return path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
    }
    private static void CheckLink(string path) {
        try {
            Require((File.GetAttributes(path) & FileAttributes.ReparsePoint) == 0,
                "Symbolic links and reparse points are unsupported: " + path);
        } catch (FileNotFoundException) { } catch (DirectoryNotFoundException) { }
    }
    private static string CanonicalPath(string path) {
        // Inspect original path components before GetFullPath removes '..'. A link
        // must not be hidden by lexical normalization of a later parent component.
        string absolute = path.Replace('/', '\\');
        string root = Path.GetPathRoot(absolute);
        if (String.IsNullOrEmpty(root)) absolute = Path.Combine(Environment.CurrentDirectory, absolute);
        else if (root == "\\") absolute = Path.GetPathRoot(Environment.CurrentDirectory) + absolute.TrimStart('\\');
        else Require(!root.EndsWith(":", StringComparison.Ordinal), "Drive-relative paths are unsupported.");
        root = Path.GetPathRoot(absolute);
        string cursor = root;
        CheckLink(cursor);
        foreach (string component in absolute.Substring(root.Length).Split('\\')) {
            if (component.Length == 0 || component == ".") continue;
            if (component == "..") {
                DirectoryInfo parent = Directory.GetParent(cursor);
                if (parent != null) cursor = parent.FullName;
            } else cursor = Path.Combine(cursor, component);
            CheckLink(cursor);
        }
        string result = Path.GetFullPath(path);
        RejectLinks(result);
        return result;
    }
    private static void RejectLinks(string path) {
        string cursor = Path.GetFullPath(path);
        while (!String.IsNullOrEmpty(cursor)) {
            CheckLink(cursor);
            cursor = Path.GetDirectoryName(cursor);
        }
    }
    private static string DecodeName(byte[] bytes) {
        string name = Names.GetString(bytes);
        Require(Names.GetBytes(name).SequenceEqual(bytes),
            "Noncanonical CP932 filename bytes cannot be preserved by this creator.");
        return name;
    }
    private static string SafeName(string value, bool flat) {
        Require(!String.IsNullOrEmpty(value), "Empty entry name.");
        value = value.Replace('/', '\\');
        Require(!Path.IsPathRooted(value) && !value.Contains(":"), "Rooted entry path: " + value);
        string[] parts = value.Split('\\');
        Require(!flat || parts.Length == 1, "NOA subset is flat; nested entry rejected.");
        foreach (string part in parts) {
            Require(part.Length > 0 && part != "." && part != ".." && part.Length <= 255 &&
                !part.EndsWith(".", StringComparison.Ordinal) && !part.EndsWith(" ", StringComparison.Ordinal) &&
                part.IndexOfAny(Path.GetInvalidFileNameChars()) < 0,
                "Unsafe or unsupported entry name: " + value);
            string stem = part.Split('.')[0].ToUpperInvariant();
            Require(stem != "CON" && stem != "PRN" && stem != "AUX" && stem != "NUL" &&
                !(stem.Length == 4 && (stem.StartsWith("COM", StringComparison.Ordinal) ||
                    stem.StartsWith("LPT", StringComparison.Ordinal)) && stem[3] >= '1' && stem[3] <= '9'),
                "Windows device name is unsupported: " + value);
        }
        Require(Names.GetString(Names.GetBytes(value)) == value, "Filename does not roundtrip in CP932.");
        return value;
    }
    private static void ValidateEntries(List<Entry> entries, bool flat) {
        var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (Entry entry in entries) {
            entry.name = SafeName(entry.name, flat);
            Require(paths.Add(entry.name), "Duplicate entry name: " + entry.name);
        }
        foreach (string path in paths) {
            string parent = Path.GetDirectoryName(path);
            while (!String.IsNullOrEmpty(parent)) {
                Require(!paths.Contains(parent), "File/directory collision: " + path);
                parent = Path.GetDirectoryName(parent);
            }
        }
    }
    private static List<Entry> Read(string format, string path) {
        Require(File.Exists(path), "Input archive does not exist.");
        long length = new FileInfo(path).Length;
        Require(length <= Int32.MaxValue, "This upstream subset only handles archives up to 2 GiB - 1.");
        using (var stream = File.OpenRead(path))
        using (var reader = new BinaryReader(stream)) {
            var entries = format == "ns2" ? ReadNs2(reader, length) : ReadNoa(reader, length);
            ValidateEntries(entries, format == "noa");
            return entries;
        }
    }
    private static List<Entry> ReadNs2(BinaryReader reader, long length) {
        Require(length >= 5, "Truncated NS2 header.");
        long dataOffset = reader.ReadUInt32();
        Require(dataOffset >= 5 && dataOffset <= length, "Invalid/encrypted NS2 index.");
        var entries = new List<Entry>();
        long payloadSize = 0;
        while (reader.BaseStream.Position < dataOffset - 1) {
            Require(reader.ReadByte() == 0x22, "NS2 name must start with quote.");
            var bytes = new List<byte>();
            bool terminated = false;
            while (reader.BaseStream.Position < dataOffset - 1) {
                byte value = reader.ReadByte();
                if (value == 0x22) { terminated = true; break; }
                bytes.Add(value);
            }
            Require(terminated && reader.BaseStream.Position + 4 <= dataOffset - 1,
                "Truncated NS2 name/size.");
            long size = reader.ReadUInt32();
            Require(size <= Int32.MaxValue, "NS2 member too large for upstream reader.");
            entries.Add(new Entry { name = DecodeName(bytes.ToArray()), offset = payloadSize, size = size });
            payloadSize = checked(payloadSize + size);
            Require(payloadSize <= length, "NS2 payload exceeds archive.");
        }
        Require(reader.BaseStream.Position == dataOffset - 1 && reader.ReadByte() == (byte)'e',
            "Invalid NS2 index terminator.");
        Require(dataOffset + payloadSize == length, "NS2 data size/trailing bytes mismatch.");
        foreach (Entry entry in entries) entry.offset += dataOffset;
        return entries;
    }
    private static List<Entry> ReadNoa(BinaryReader reader, long length) {
        Require(length >= 84, "Truncated NOA header.");
        Require(reader.ReadBytes(16).SequenceEqual(NoaMagic) &&
            Encoding.ASCII.GetString(reader.ReadBytes(18)) == "ERISA-Archive file", "Unsupported NOA signature/version.");
        reader.BaseStream.Position = 56;
        Require(reader.ReadUInt64() == (ulong)(length - 64), "NOA declared size mismatch.");
        Require(Encoding.ASCII.GetString(reader.ReadBytes(8)) == "DirEntry", "Missing NOA DirEntry.");
        ulong indexSize = reader.ReadUInt64();
        Require(indexSize >= 4 && indexSize <= (ulong)(length - 80), "Invalid NOA index size.");
        long indexEnd = 80 + (long)indexSize;
        uint count = reader.ReadUInt32();
        Require(count <= (indexSize - 4) / 41, "Invalid NOA entry count.");
        var entries = new List<Entry>();
        for (uint i = 0; i < count; i++) {
            Require(reader.BaseStream.Position + 40 <= indexEnd, "Truncated NOA entry.");
            ulong size = reader.ReadUInt64();
            uint attributes = reader.ReadUInt32();
            uint encoding = reader.ReadUInt32();
            ulong relativeOffset = reader.ReadUInt64();
            Require(attributes == 0 && encoding == 0, "NOA subset rejects directories, compression and encryption.");
            Require(size <= Int32.MaxValue && relativeOffset <= Int32.MaxValue,
                "NOA member exceeds upstream size limit.");
            reader.ReadBytes(8); // Timestamp is read but not preserved by the raw creator.
            uint extraLength = reader.ReadUInt32();
            Require(extraLength <= (ulong)(indexEnd - reader.BaseStream.Position - 4), "Invalid NOA extra metadata size.");
            reader.BaseStream.Position += extraLength;
            uint nameLength = reader.ReadUInt32();
            Require(nameLength >= 2 && nameLength <= (ulong)(indexEnd - reader.BaseStream.Position), "Invalid NOA name size.");
            string name = DecodeName(reader.ReadBytes((int)nameLength - 1));
            Require(reader.ReadByte() == 0, "NOA name lacks NUL terminator.");
            long recordOffset = (long)relativeOffset + 64;
            Require(recordOffset >= indexEnd && recordOffset + 16 <= length &&
                (long)size <= length - recordOffset - 16, "NOA entry outside content area.");
            long next = reader.BaseStream.Position;
            reader.BaseStream.Position = recordOffset;
            Require(Encoding.ASCII.GetString(reader.ReadBytes(8)) == "filedata" &&
                reader.ReadUInt64() == size, "Invalid NOA filedata record.");
            entries.Add(new Entry { name = name, offset = recordOffset + 16, size = (long)size });
            reader.BaseStream.Position = next;
        }
        Require(reader.BaseStream.Position == indexEnd, "NOA index boundary mismatch.");
        long end = indexEnd;
        foreach (Entry entry in entries.OrderBy(e => e.offset)) {
            Require(entry.offset - 16 >= end, "Overlapping NOA filedata records.");
            end = entry.offset + entry.size;
        }
        return entries;
    }
    private static void NewOutput(string output) {
        RejectLinks(output);
        Require(!File.Exists(output) && !Directory.Exists(output), "Output already exists.");
        Require(output.Length <= 259, "Output path exceeds .NET Framework path limit.");
    }
    private static void Pack(string format, string input, string output) {
        Require(Directory.Exists(input), "Input directory does not exist.");
        NewOutput(output);
        Require(!output.StartsWith(Prefix(input), StringComparison.OrdinalIgnoreCase), "Output must be outside input directory.");
        var entries = new List<Entry>();
        var pending = new Stack<string>(); pending.Push(input);
        long total = 0;
        while (pending.Count != 0) {
            string current = pending.Pop(); RejectLinks(current);
            foreach (string child in Directory.GetDirectories(current)) {
                RejectLinks(child);
                Require(format != "noa", "NOA raw creator is flat; subdirectory rejected.");
                pending.Push(child);
            }
            foreach (string file in Directory.GetFiles(current)) {
                RejectLinks(file);
                long size = new FileInfo(file).Length;
                Require(size <= Int32.MaxValue, "Member exceeds upstream size limit.");
                string name = file.Substring(Prefix(input).Length);
                entries.Add(new Entry { name = name, size = size });
                total = checked(total + size + Names.GetByteCount(name) + 80);
                Require(total < Int32.MaxValue - 100, "Archive exceeds upstream 2 GiB size limit.");
            }
        }
        Require(entries.Count > 0, "Input directory has no files.");
        ValidateEntries(entries, format == "noa");
        string parent = Path.GetDirectoryName(output); Directory.CreateDirectory(parent);
        string temporary = Path.Combine(parent, ".galarc-" + Guid.NewGuid().ToString("N") + ".tmp");
        try {
            if (format == "ns2") new ArcFormats.NScripter.NS2().Pack(input, temporary);
            else new ArcFormats.EntisGLS.NOA().Pack(input, temporary);
            var actual = Read(format, temporary);
            Require(actual.Count == entries.Count, "Created archive entry count mismatch.");
            File.Move(temporary, output);
            Console.WriteLine(output);
        } finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
    private static void Extract(string format, string input, string output, List<Entry> entries) {
        NewOutput(output);
        foreach (Entry entry in entries) {
            string path = Path.GetFullPath(Path.Combine(output, entry.name));
            Require(path.StartsWith(Prefix(output), StringComparison.OrdinalIgnoreCase) && path.Length <= 259,
                "Extraction path outside output or too long.");
        }
        string parent = Path.GetDirectoryName(output); Directory.CreateDirectory(parent);
        string temporary = Path.Combine(parent, ".galarc-" + Guid.NewGuid().ToString("N"));
        try {
            if (format == "ns2") new ArcFormats.NScripter.NS2().Unpack(input, temporary);
            else new ArcFormats.EntisGLS.NOA().Unpack(input, temporary);
            Directory.Move(temporary, output);
            Console.WriteLine(output);
        } finally {
            if (Directory.Exists(temporary) && Path.GetFullPath(temporary).StartsWith(Prefix(parent), StringComparison.OrdinalIgnoreCase))
                Directory.Delete(temporary, true);
        }
    }
}
