#include "config-view-endpoint.h"
struct view_serve_context {
 unsigned int lifetime;
 int (*capture)(unsigned int,struct wr_iot_config_view *,char[33]);
};
static int serve_view(int fd,uid_t uid,void *context)
{
 struct view_serve_context *view=context;
 return wr_iot_config_view_serve_once(fd,uid,view->lifetime,view->capture);
}
int wr_iot_config_view_endpoint_step(struct wr_iot_status_endpoint *endpoint,unsigned int lifetime,
 int (*capture)(unsigned int,struct wr_iot_config_view *,char[33]))
{
 struct view_serve_context context={lifetime,capture};
 return capture&&lifetime&&lifetime<=300?wr_iot_status_endpoint_step_dispatch(endpoint,serve_view,&context):0;
}
struct view_query_context {struct wr_iot_config_view view;char revision[33];};
static int query_view(int fd,pid_t pid,uid_t uid,void *context)
{
 struct view_query_context *view=context;
 return wr_iot_config_view_query(fd,pid,uid,&view->view,view->revision);
}
int wr_iot_config_view_endpoint_query(const char *path,pid_t pid,uid_t uid,
 struct wr_iot_config_view *out,char revision[33])
{
 struct view_query_context context={0};int ok=0;
 if(!out||!revision)goto done;
 ok=wr_iot_status_endpoint_query_dispatch(path,pid,uid,query_view,&context);
 if(ok){*out=context.view;memcpy(revision,context.revision,sizeof(context.revision));}
 done:wr_iot_saved_wipe(&context,sizeof(context));return ok;
}
