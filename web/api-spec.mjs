const object=(properties,required=Object.keys(properties))=>({type:'object',properties,required,additionalProperties:false});
const str={type:'string'};
const nullable=type=>({type:[type,'null']});
const timestamp={type:'string',format:'date-time'};
export const jobSchema={
  $schema:'https://json-schema.org/draft/2020-12/schema',
  $id:'https://agtxiv.org/schema/web/1.0/job.schema.json',
  title:'AgtXIv source-analysis job',
  description:'Retained processing state; COMPLETED means candidate extraction finished, not scientific acceptance.',
  ...object({api_version:{const:'1.0'},id:{type:'string',format:'uuid'},arxiv:str,
    status:{enum:['QUEUED','FETCHING','ANALYZING','COMPLETED','FAILED','INTERRUPTED']},
    stages:{const:['QUEUED','FETCHING','ANALYZING','COMPLETED']},created_at:timestamp,updated_at:timestamp,
    revision:{type:'integer',minimum:0},result_url:nullable('string'),analysis_id:nullable('string'),parent_id:nullable('string'),
    error:{anyOf:[{type:'null'},object({code:str,message:str})]},scientific_assessment:{const:'NOT_PERFORMED'}}),
  allOf:[{if:{properties:{status:{const:'COMPLETED'}}},then:{properties:{result_url:{type:'string',pattern:'^/api/v1/jobs/'},analysis_id:{type:'string',minLength:1},error:{type:'null'}}}},
    {if:{properties:{status:{enum:['FAILED','INTERRUPTED']}}},then:{properties:{error:{type:'object'},result_url:{type:'null'}}}}],
};

const schemaRef=name=>({$ref:`#/components/schemas/${name}`});
const response=(description,schema)=>({description,content:{'application/json':{schema}}});
const errors=Object.fromEntries([[400,'Malformed input'],[403,'Foreign-origin submission rejected'],[405,'Unsupported request method'],[500,'Unexpected server failure'],[404,'Unknown job, paper, or resource'],[409,'Result not ready or retry not allowed'],[413,'Request body too large'],[415,'Unsupported content type'],[429,'Intake rate or capacity limit'],[503,'Storage or result unavailable']].map(([code,desc])=>[code,response(desc,schemaRef('Error'))]));
const jobParameter={name:'id',in:'path',required:true,schema:{type:'string',format:'uuid'},description:'Job UUID returned by POST /jobs.'};
export const openapi={
  openapi:'3.1.0',info:{title:'AgtXIv source-analysis and reader API',version:'1.0.0',description:'Actual arXiv source intake, retained candidate analyses, and read-only research records. Jobs execute bounded static TeX analysis. They do not run TeX, mathematical proofs, scientific review, or knowledge admission. Unversioned input is resolved to an exact version before downloading source.'},
  servers:[{url:'/'}],
  tags:[{name:'Analysis'},{name:'Reader'},{name:'Contracts'}],
  paths:{
    '/api/v1/health':{get:{operationId:'readServiceHealth',tags:['Analysis'],summary:'Read service configuration status',responses:{200:response('Configuration available',object({api_version:{const:'1.0'},status:{enum:['READY','READ_ONLY']},analysis_method:{const:'BOUNDED_SOURCE_CANDIDATE_EXTRACTION'},scientific_assessment:{const:'NOT_PERFORMED'}}))}}},
    '/api/v1/jobs':{post:{operationId:'submitArxivPaper',tags:['Analysis'],summary:'Fetch and analyze a new arXiv source',description:'Maximum JSON body 2 KiB. Source archives are limited to 8 MiB downloaded, 16 MiB expanded, 2 MiB per file, 4 MiB combined TeX and 240 candidates. All processing budgets and their byte/millisecond units are listed in x-agtxiv-processing-limits and retained in each analysis result. The service admits at most one new job per 3.5 seconds and three recent active jobs. Processing continues after the response. Poll the Location URL. Exact versions are recommended; unversioned identifiers resolve through arXiv metadata.',requestBody:{required:true,content:{'application/json':{schema:object({arxiv:{type:'string',minLength:1,maxLength:256}}),examples:{versioned:{value:{arxiv:'2405.08863v1'}},resolve:{value:{arxiv:'https://arxiv.org/abs/1706.03762'}}}}}},responses:{202:{...response('Job created and execution scheduled',schemaRef('Job')),headers:{Location:{schema:str,description:'Relative status URL'}}},...errors}}},
    '/api/v1/jobs/{id}':{get:{operationId:'readAnalysisJob',tags:['Analysis'],summary:'Read actual processing state',description:'GET does not modify the stored job. A nonterminal job with no update for 120 seconds is projected as INTERRUPTED. This is an observation of missing progress, not a confirmed worker termination: the earlier attempt may still finish. Retry creates a new retained attempt.',parameters:[jobParameter],responses:{200:response('Current job view',schemaRef('Job')),...errors}}},
    '/api/v1/jobs/{id}/result':{get:{operationId:'readAnalysisResult',tags:['Analysis'],summary:'Read the exact retained source analysis',description:'The result bytes are checked against their content-addressed storage key. Contains bounded source excerpts, byte anchors, candidate statements/equations, textual reference cues, unclassified ranges, source hashes and all six NO_ASSESSMENT values.',parameters:[jobParameter],responses:{200:response('Immutable completed candidate analysis',schemaRef('Analysis')),...errors}}},
    '/api/v1/jobs/{id}/retry':{post:{operationId:'retryAnalysisAsNewJob',tags:['Analysis'],summary:'Create a new attempt for a failed or interrupted analysis',description:'Preserves the original job and binds the new job through parent_id. Existing results are never overwritten.',parameters:[jobParameter],requestBody:{required:true,content:{'application/json':{schema:object({})}}},responses:{202:response('New attempt created',schemaRef('Job')),...errors}}},
    '/api/v1/library':{get:{operationId:'readResearchLibrary',tags:['Reader'],summary:'Read the curated collection and its contract catalog',parameters:[{name:'q',in:'query',required:false,schema:{type:'string',maxLength:200},description:'Case-insensitive substring search over title, arXiv identifier and retained interpretations.'}],responses:{200:response('Exact-input reader projection',schemaRef('Library')),...errors}}},
    '/api/v1/papers/{slug}':{get:{operationId:'readCuratedPaper',tags:['Reader'],summary:'Read one curated paper',parameters:[{name:'slug',in:'path',required:true,schema:str}],responses:{200:response('Paper projection, with original legacy status retained',object({api_version:{const:'1.0'},paper:schemaRef('Paper')})),...errors}}},
    '/api/v1/schemas':{get:{operationId:'readRecordCatalog',tags:['Contracts'],summary:'List all 64 V3 record families and their payload field descriptions',responses:{200:response('Version-pinned schema catalog',object({api_version:{const:'1.0'},schema_bundle_hash:str,records:{type:'array',items:schemaRef('RecordFamily')}})),...errors}}},
    '/schemas/v3/{filename}':{get:{operationId:'downloadV3Schema',tags:['Contracts'],summary:'Download an original V3 schema or manifest',description:'Schema $id URIs are identifiers. Resolve canonical references through the downloaded local catalog; do not assume agtxiv.org serves schema bytes.',parameters:[{name:'filename',in:'path',required:true,schema:str,example:'source-snapshot.schema.json'}],responses:{200:response('Unmodified source schema or manifest',{type:'object'}),404:errors[404]}}},
  },
  components:{schemas:{
    Job:{$ref:'job.schema.json'},Analysis:{$ref:'analysis.schema.json'},
    Error:object({api_version:{const:'1.0'},error:object({code:str,message:str,request_id:{type:'string',format:'uuid'}})}),
    RecordRef:object({record_type:str,record_id:str,revision:{type:'integer',minimum:1},content_hash:{type:'string',pattern:'^sha256:[a-f0-9]{64}$'}}),
    Field:object({name:str,type:{anyOf:[str,{type:'array',items:str}]},required:{type:'boolean'},description:str,definition:{type:'object'}}),
    RecordFamily:object({record_type:str,schema:str,title:str,roadmap_tasks:{type:'array',items:str},description:str,fields:{type:'array',items:schemaRef('Field')},sha256:str,url:str}),
    Paper:{type:'object',required:['slug','title','arxiv','source_url','legacy_status','provenance','view','imports','claims','note'],properties:{slug:str,title:str,arxiv:str,source_url:{type:'string',format:'uri'},legacy_status:str,provenance:object({path:str,sha256:str}),view:{enum:['LEGACY_REFERENCE','V3_CANDIDATE_READER']},imports:{type:'array',items:{type:'object'}},claims:{type:'array',items:{$ref:'#/components/schemas/CuratedCandidate'}},note:str,records_url:str,open_questions:{type:'array',items:str},obligations:{type:'array',items:{type:'object'}},package_ref:{type:'object'},source_ref:schemaRef('RecordRef'),observed_at:timestamp},additionalProperties:false},
    CuratedCandidate:{type:'object',required:['id','interpretation','record_ref','anchors','conditions','dependencies','assessments'],properties:{id:str,interpretation:str,record_ref:schemaRef('RecordRef'),title:str,intuition:str,formula:nullable('string'),editorial_explanation:{const:true},anchors:{type:'array',items:{type:'object'}},conditions:{type:'array',items:str},dependencies:{type:'array',items:str},unknowns:{type:'array',items:str},assessments:{type:'array',items:object({axis:str,status:{const:'NOT_ASSESSED'}})},data_class:str,verification:str},additionalProperties:false},
    Library:object({api_version:{const:'1.0'},kind:{const:'AGTXIV_READER_LIBRARY'},status:{const:'RESEARCH_PREVIEW'},schema_bundle_hash:str,papers:{type:'array',items:schemaRef('Paper')},schemas:{type:'array',items:schemaRef('RecordFamily')},evidence:object({inventory:str,records:str}),scientific_acceptance:{const:false}}),
  }},
};
