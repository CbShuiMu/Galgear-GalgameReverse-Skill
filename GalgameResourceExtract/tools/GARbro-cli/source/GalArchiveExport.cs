// SPDX-License-Identifier: MIT
// Resource stream API from GARbro (morkt and contributors).
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using GameRes;
using GameRes.Formats.Musica;

static class GalArchiveExport
{
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    static readonly UTF8Encoding Utf8 = new UTF8Encoding(false);

    [STAThread]
    static int Main(string[] args)
    {
        Console.OutputEncoding = Utf8;
        bool listPaz = args.Length == 1 && args[0] == "--paz-schemes";
        if (!listPaz && (args.Length < 2 || args.Length > 4))
        {
            Console.Error.WriteLine("Usage: GalArchiveExport ARCHIVE NEW_OUTPUT_DIRECTORY [ARCHIVE_TAG [PAZ_SCHEME]]");
            Console.Error.WriteLine("       GalArchiveExport --paz-schemes");
            return 2;
        }

        try
        {
            var catalog = FormatCatalog.Instance;
            using (var schemes = File.OpenRead(Path.Combine(catalog.DataDirectory, "Formats.dat")))
                catalog.DeserializeScheme(schemes);

            if (listPaz)
            {
                var paz = catalog.ArcFormats.OfType<PazOpener>().Single();
                Console.WriteLine(Json.Serialize(paz.KnownTitles.Keys.OrderBy(name => name).ToArray()));
                return 0;
            }

            string output = Path.GetFullPath(args[1]);
            if (Directory.Exists(output) || File.Exists(output))
                throw new IOException("output already exists");

            string inputPath = Path.GetFullPath(args[0]);
            var format = args.Length >= 3 ? catalog.ArcFormats.SingleOrDefault(f =>
                string.Equals(f.Tag, args[2], StringComparison.OrdinalIgnoreCase)) : null;
            if (args.Length >= 3 && format == null)
                throw new ArgumentException("unknown or ambiguous archive tag");
            using (var view = format == null ? null : new ArcView(inputPath))
            {
                if (args.Length == 4)
                {
                    var paz = format as PazOpener;
                    PazScheme scheme;
                    if (paz == null || !paz.KnownTitles.TryGetValue(args[3], out scheme))
                        throw new ArgumentException("unknown PAZ scheme or tag is not PAZ");
                    paz.KnownSchemes[view.View.ReadUInt32(0)] = scheme;
                }
                using (var archive = format == null ? ArcFile.TryOpen(inputPath) : format.TryOpen(view))
                    return Export(archive, output);
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
            return 1;
        }
    }

    static int Export(ArcFile archive, string output)
    {
        if (archive == null || archive.Dir.Count == 0)
            throw new InvalidDataException("archive not recognized or index is empty");

        Directory.CreateDirectory(output);
        int failed = 0;
        using (var log = new StreamWriter(Path.Combine(output, "manifest.jsonl"), false, Utf8))
        {
            log.AutoFlush = true;
            int index = 0;
            foreach (var entry in archive.Dir)
            {
                string file = index.ToString("D8") + ".bin";
                string target = Path.Combine(output, file);
                string temporary = target + ".partial";
                try
                {
                    string digest;
                    long size;
                    using (var input = archive.OpenEntry(entry))
                    using (var stream = new FileStream(temporary, FileMode.CreateNew))
                    using (var sha = SHA256.Create())
                    {
                        using (var hashing = new CryptoStream(stream, sha, CryptoStreamMode.Write))
                        {
                            input.CopyTo(hashing);
                            hashing.FlushFinalBlock();
                            size = stream.Length;
                        }
                        digest = BitConverter.ToString(sha.Hash).Replace("-", "").ToLowerInvariant();
                    }

                    if (entry.Size > 0 && size == 0)
                        throw new InvalidDataException("nonempty stored member produced an empty payload");

                    File.Move(temporary, target);
                    log.WriteLine(Json.Serialize(new { status = "ok", entry = index, name = entry.Name,
                        offset = entry.Offset, stored_size = entry.Size, size, sha256 = digest, file,
                        layer = "logical" }));
                }
                catch (Exception ex)
                {
                    if (File.Exists(temporary))
                        File.Delete(temporary);
                    ++failed;
                    log.WriteLine(Json.Serialize(new { status = "error", entry = index, name = entry.Name,
                        offset = entry.Offset, stored_size = entry.Size, error = ex.Message }));
                }
                ++index;
            }
        }
        Console.WriteLine(Json.Serialize(new { format = archive.Tag, listed = archive.Dir.Count, failed }));
        return failed == 0 ? 0 : 1;
    }
}
