// Batch front end for GARbro/GameRes (MIT). No game execution or input writes.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using GameRes;
class GalImageExport {
 public class Job { public string mode,source,output,filter; public string[] files; public int seconds=240; public bool all=false; public bool duplicatesOnly=false; }
 static JavaScriptSerializer json=new JavaScriptSerializer(){MaxJsonLength=100000000};
 static StreamWriter log; static Stopwatch timer;static int budget;static string output;static int decodedCount;
 static void Emit(object o){log.WriteLine(json.Serialize(o));log.Flush();}
 static string Hash(string p){using(var f=File.OpenRead(p))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
 static string Target(string root,string name){
  name=name.Replace('/',Path.DirectorySeparatorChar);
  if(Path.IsPathRooted(name)||name.Contains(":"))throw new Exception("absolute member path");
  var p=Path.GetFullPath(Path.Combine(root,name));var r=Path.GetFullPath(root)+Path.DirectorySeparatorChar;
  if(!p.StartsWith(r,StringComparison.OrdinalIgnoreCase))throw new Exception("member outside output");
  return p;
 }
 static bool Expired(){return timer.Elapsed.TotalSeconds>=budget;}
 static void Png(ImageData image,string name,object origin){
  if(image==null)throw new Exception("image format not recognized");
  if((long)image.Width*image.Height>200000000)throw new Exception("pixel limit");
  string path=Target(Path.Combine(output,"png"),name+".png");Directory.CreateDirectory(Path.GetDirectoryName(path));
  using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write))ImageFormat.Png.Write(f,image);
  Emit(new{kind="png",name=name,path=path,sha256=Hash(path),width=image.Width,height=image.Height,bpp=image.BPP,offset_x=image.OffsetX,offset_y=image.OffsetY,origin=origin});
  if(++decodedCount%24==0){GC.Collect();GC.WaitForPendingFinalizers();}
 }
 static void Decode(string source,string name,ArcFile arc=null,Entry entry=null){
  if(Expired()){Emit(new{kind="decode_deferred",name=name,reason="time budget"});return;}
  try {
   // G00 v2 and HG3 can contain multiple subimages. Preserve every frame and its offset.
   string ext=Path.GetExtension(name).ToLowerInvariant();
   if(ext==".g00"||ext==".hg3"||ext==".hg2"||ext==".pimg"){
    using(var inner=ArcFile.TryOpen(source))if(inner!=null){
     int n=0;foreach(var e in inner.Dir){if(Expired()){Emit(new{kind="decode_deferred",name=name,reason="frame budget"});break;}try{using(var d=inner.OpenImage(e))Png(d.Image,name+".frames/"+(n++).ToString("D5")+"-"+Path.GetFileName(e.Name),new{container=name,member=e.Name,offset=e.Offset,size=e.Size});}catch(Exception x){Emit(new{kind="decode_error",name=name,frame=e.Name,error=x.Message});}}
     Emit(new{kind="frame_container",name=name,format=inner.Tag,frames=inner.Dir.Count});return;
    }
   }
   if(arc!=null){using(var d=arc.OpenImage(entry))Png(d.Image,name,new{member=entry.Name,offset=entry.Offset,size=entry.Size});}
   else{using(var f=BinaryStream.FromFile(source))Png(ImageFormat.Read(f),name,new{source=source});}
  }catch(Exception e){Emit(new{kind="decode_error",name=name,error=e.Message});}
 }
 static bool Image(Entry e){return e.Type=="image"||Regex.IsMatch(e.Name,@"(?i)\.(png|jpe?g|bmp|webp|tga|g00|g01|pdt|rct|rc8|hg[23]|dwq|hzc|hzc1|nvsg|tex|pimg|eri|ycg|psb)$");}
 [STAThread] static int Main(string[] args){
  if(args.Length!=1){Console.WriteLine("GalImageExport JOB.json (archive/files; separate raw and PNG with frame offsets)");return 2;}
  var job=json.Deserialize<Job>(File.ReadAllText(args[0],Encoding.UTF8));output=Path.GetFullPath(job.output);
  if(Directory.Exists(output)||File.Exists(output)){Console.Error.WriteLine("Output already exists");return 2;}
  Directory.CreateDirectory(output);timer=Stopwatch.StartNew();budget=job.seconds;
  using(log=new StreamWriter(Path.Combine(output,"manifest.jsonl"),false,new UTF8Encoding(false))){
   try{
    try{using(var s=File.OpenRead(Path.Combine(FormatCatalog.Instance.DataDirectory,"Formats.dat")))FormatCatalog.Instance.DeserializeScheme(s);}catch(Exception e){Emit(new{kind="scheme_notice",error=e.Message});}
    if(job.mode=="files"||job.mode=="decode"){
     var raw=new List<Tuple<string,string>>();foreach(string source in job.files){
      if(Expired()){Emit(new{kind="raw_deferred",source=source,reason="time budget"});continue;}
      string name=source.Substring(Path.GetFullPath(job.source).TrimEnd('\\').Length).TrimStart('\\');string path=Target(Path.Combine(output,"raw"),name);
      try{if(job.mode=="decode")path=source;else{Directory.CreateDirectory(Path.GetDirectoryName(path));File.Copy(source,path,false);}string hash=Hash(path);if(hash!=Hash(source))throw new Exception("copy hash differs");Emit(new{kind="raw",name=name,path=path,source=source,size=new FileInfo(path).Length,sha256=hash});raw.Add(Tuple.Create(path,name));}catch(Exception e){Emit(new{kind="raw_error",name=name,error=e.Message});}
     }foreach(var p in raw)Decode(p.Item1,p.Item2);
    }else if(job.mode=="archive"){
     using(var arc=ArcFile.TryOpen(job.source)){
      if(arc==null)throw new Exception("archive format not recognized");
      var selected=arc.Dir.Where(e=>(job.all||Image(e))&&(String.IsNullOrEmpty(job.filter)||Regex.IsMatch(e.Name,job.filter))).ToArray();
      Emit(new{kind="archive",source=job.source,format=arc.Tag,total=arc.Dir.Count,selected=selected.Length});
      var raw=new List<Tuple<Entry,string,string>>();var seenNames=new HashSet<string>(StringComparer.OrdinalIgnoreCase);int ordinal=0;foreach(var e in selected){
       int index=ordinal++;bool duplicate=!seenNames.Add(e.Name);if(job.duplicatesOnly&&!duplicate)continue;
       string outputName=duplicate?"__duplicate_members/"+index.ToString("D8")+"/"+e.Name:e.Name;
       if(Expired()){Emit(new{kind="raw_deferred",name=e.Name,reason="time budget"});continue;}
       try{string path=Target(Path.Combine(output,"raw"),outputName);Directory.CreateDirectory(Path.GetDirectoryName(path));using(var input=arc.OpenEntry(e))using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write))input.CopyTo(f);Emit(new{kind="raw",name=outputName,original_name=e.Name,entry_index=index,duplicate_name=duplicate,path=path,size=new FileInfo(path).Length,sha256=Hash(path),archive_offset=e.Offset,stored_size=e.Size,layer="logical-member; original archive retained"});raw.Add(Tuple.Create(e,path,outputName));}catch(Exception x){Emit(new{kind="raw_error",name=e.Name,entry_index=index,error=x.Message});}
      }foreach(var p in raw)Decode(p.Item2,p.Item3,arc,p.Item1);
     }
    }else throw new Exception("unknown mode");
    Emit(new{kind="complete",seconds=timer.Elapsed.TotalSeconds});return 0;
   }catch(Exception e){Emit(new{kind="fatal",error=e.ToString()});return 1;}
  }
 }
}
