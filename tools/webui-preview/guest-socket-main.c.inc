#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#include <signal.h>
int main(void)
{
 int listener=socket(AF_INET,SOCK_STREAM,0);assert(listener>=0);
 struct sockaddr_in address={0};address.sin_family=AF_INET;address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
 assert(!bind(listener,(struct sockaddr *)&address,sizeof(address)));assert(!listen(listener,16));
 socklen_t size=sizeof(address);assert(!getsockname(listener,(struct sockaddr *)&address,&size));
 reset_endpoint(1,0);signal(SIGPIPE,SIG_IGN);
 printf("PORT %u\n",ntohs(address.sin_port));fflush(stdout);
 for(;;){
  int fd=accept(listener,NULL,NULL);if(fd<0)continue;
  struct timeval timeout={3,0};setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
  FILE *stream=fdopen(fd,"r+");if(!stream){close(fd);continue;}setvbuf(stream,NULL,_IONBF,0);
  conn_item_t item={0};item.fd=fd;login_fixture=3;handle_request(stream,&item);fflush(stream);fclose(stream);
 }
}
