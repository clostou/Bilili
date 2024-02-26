//////////////////////////////////////////////////////////////////////////////
//
//
//  --- m4sMerge.c ---
//
//
//  Function：Mux .m4s file (alse cover and closed caption) downloaded
//                  from Bilibili to MP4 format. Use FFmpeg API.
//
//  Author: Yangwang (GitHub@clostou)
//
//  Creation Date: 2023/4/4
//
//  Last Modified: 2023/4/4
//
//
//////////////////////////////////////////////////////////////////////////////

#include <Windows.h>
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavutil/timestamp.h>

#define MAX_PATH_LENGTH 256
//#define DEBUG


typedef struct CopyStream {
	AVFormatContext* ctx;
	AVStream* st_from;
	AVStream* st_to;
}CopyStream;


void stream_free(CopyStream** cs)
{
	if (*cs) {
		if ((*cs)->ctx) {
			avformat_close_input(&(*cs)->ctx);
		}
		(*cs)->st_from = NULL;
		(*cs)->st_to = NULL;
		free(*cs);
		*cs = NULL;
	}
}


int read_media(CopyStream** cs, const char* filename, enum AVMediaType type)
{
	int ret = 0, stream_ind;
	CopyStream* stream = NULL;

	stream = (CopyStream*)calloc(1, sizeof(CopyStream));
	if (!stream) {
		ret = AVERROR(ENOMEM);
		printf("Failed allocating input context\n");
		goto end;
	}
	*cs = stream;

	ret = avformat_open_input(&stream->ctx, filename, NULL, NULL);
	if (ret < 0) {
		printf("Could not open input file '%s'\n", filename);
		goto end;
	}
#ifdef DEBUG
	printf("Open format '%s': %s\n", stream->ctx->iformat->name, stream->ctx->iformat->long_name);
#endif // DEBUG

	ret = avformat_find_stream_info(stream->ctx, NULL);
	if (ret < 0) {
		printf("Failed to retrieve input stream information\n");
		goto end;
	}
	
	stream_ind = av_find_best_stream(stream->ctx, type, -1, -1, NULL, 0);
	if (stream_ind < 0) {
		ret = stream_ind;
		printf("Could not find specific stream in input file\n");
		goto end;
	}
	stream->st_from = stream->ctx->streams[stream_ind];

end:
	return ret;
}


int write_media(AVFormatContext** ctx, const char* filename)
{
	int ret = 0;

	ret = avformat_alloc_output_context2(ctx, NULL, "mp4", filename);
	if (ret < 0) {
		printf("Failed allocating output context\n");
		goto end;
	}
#ifdef DEBUG
	printf("Write format '%s': %s\n", (*ctx)->oformat->name, (*ctx)->oformat->long_name);
#endif // DEBUG
	if (!((*ctx)->oformat->flags & AVFMT_NOFILE)) {
		ret = avio_open(&(*ctx)->pb, filename, AVIO_FLAG_WRITE);
		if (ret < 0) {
			printf("Could not open output file '%s'\n", filename);
			goto end;
		}
	}

end:
	return ret;
}


int add_stream(AVFormatContext* ctx, CopyStream* cs)
{
	int ret = 0;

	cs->st_to = avformat_new_stream(ctx, NULL);
	if (cs->st_to) {
		cs->st_to->id = ctx->nb_streams - 1;
		cs->st_to->time_base = cs->st_from->time_base;
		cs->st_to->disposition = AV_DISPOSITION_DEFAULT;
		ret = avcodec_parameters_copy(cs->st_to->codecpar, cs->st_from->codecpar);
	}
	else {
		ret = AVERROR_UNKNOWN;
	}
	if (ret < 0) {
		printf("Failed to add media stream\n");
		goto end;
	}

	ret = av_dict_copy(&cs->st_to->metadata, cs->st_from->metadata, 0);
	if (ret < 0) {
		printf("Failed to copy stream metadata\n");
		goto end;
	}

end:
	return ret;
}


typedef struct Codec {
	AVCodecContext* dec;
	AVCodecContext* enc;
}Codec;


void codec_free(Codec** co)
{
	if (*co) {
		if ((*co)->dec) {
			avcodec_free_context(&(*co)->dec);
		}
		if ((*co)->enc) {
			if ((*co)->enc->subtitle_header)
				(*co)->enc->subtitle_header = NULL;
			avcodec_free_context(&(*co)->enc);
		}
		free(*co);
		*co = NULL;
	}
}


int open_subtitle_codec(AVFormatContext* ctx, CopyStream* cs, Codec** co)
{
	int ret;
	const AVCodec* dec, * enc;
	Codec* codec;
	char* dict = NULL;

	codec = (Codec*)calloc(1, sizeof(Codec));
	if (!codec) {
		ret = AVERROR(ENOMEM);
		printf("Failed allocating subtitle codec context\n");
		goto end;
	}
	*co = codec;

	dec = avcodec_find_decoder(cs->st_from->codecpar->codec_id);
	codec->dec = avcodec_alloc_context3(dec);
	ret = avcodec_parameters_to_context(codec->dec, cs->st_from->codecpar);
	ret = avcodec_open2(codec->dec, dec, NULL);
	if (ret < 0) {
		printf("Failed to initialize subtitle decoder\n");
		goto end;
	}

	enc = avcodec_find_encoder(AV_CODEC_ID_MOV_TEXT);
	codec->enc = avcodec_alloc_context3(enc);
	if (codec->enc) {
		codec->enc->codec_tag = 0;
		codec->enc->time_base = cs->st_from->time_base;
		codec->enc->subtitle_header = codec->dec->subtitle_header;
		if (ctx->flags & AVFMT_GLOBALHEADER)
			codec->enc->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
	}
	ret = avcodec_open2(codec->enc, enc, NULL);
	if (ret < 0) {
		printf("Failed to initialize subtitle encoder\n");
		goto end;
	}

	cs->st_to = avformat_new_stream(ctx, enc);
	if (cs->st_to) {
		cs->st_to->id = ctx->nb_streams - 1;
		cs->st_to->time_base = cs->st_from->time_base;
		cs->st_to->disposition = AV_DISPOSITION_DEFAULT | AV_DISPOSITION_FORCED;
		//av_dict_set(&cs->st_to->metadata, "language", "chs", 0);
		ret = avcodec_parameters_from_context(cs->st_to->codecpar, codec->enc);
	}
	else {
		ret = AVERROR_UNKNOWN;
	}
	if (ret < 0) {
		printf("Failed to add subtitle stream\n");
		goto end;
	}

end:
	return ret;
}


int transcode_subtitle(Codec* co, AVPacket* pkt)
{
	int ret, got_output = 1, stream_ind, subtitle_size;
	AVSubtitle subtitle = { 0 };

	stream_ind = pkt->stream_index;
	ret = avcodec_decode_subtitle2(co->dec, &subtitle, &got_output, pkt);
	if (ret < 0) goto end;
	subtitle.pts = av_rescale_q(pkt->pts, pkt->time_base, AV_TIME_BASE_Q);
	subtitle.start_display_time = 0;
	subtitle.end_display_time = (uint32_t)av_rescale_q(pkt->duration, pkt->time_base, (AVRational) { 1, 1000 });

	ret = av_new_packet(pkt, 1024 * 1024);
	if (ret < 0) goto end;
	subtitle_size = avcodec_encode_subtitle(co->enc, pkt->data, pkt->size, &subtitle);
	if (subtitle_size < 0) {
		ret = subtitle_size;
		goto end;
	}
	pkt->stream_index = stream_ind;
	pkt->pos = -1;
	pkt->time_base = co->enc->time_base;
	pkt->pts = av_rescale_q(subtitle.pts, AV_TIME_BASE_Q, pkt->time_base);
	pkt->dts = pkt->pts;
	pkt->duration = av_rescale_q(subtitle.end_display_time, (AVRational) { 1, 1000 }, pkt->time_base);
	av_shrink_packet(pkt, subtitle_size);

end:
	avsubtitle_free(&subtitle);

	return ret;
}


int read_packet(CopyStream* cs, AVPacket* pkt)
{
	int ret = 0;
	
	av_packet_unref(pkt);
	ret = av_read_frame(cs->ctx, pkt);
	pkt->stream_index = cs->st_to->id;
	pkt->pos = -1;
	pkt->time_base = cs->st_to->time_base;
	
	return ret;
}


int write_packet(AVFormatContext* ctx, AVPacket* pkt)
{
	return av_interleaved_write_frame(ctx, pkt);
}


int compare_dts(AVPacket* pkt_a, AVPacket* pkt_b)
{
	return av_compare_ts(pkt_a->dts, pkt_a->time_base, pkt_b->dts, pkt_b->time_base);
}


int A2U(const char* ansiiCode, char* utf8Code)
{
	int cchUnicode, cbUtf8 = 0;
	WCHAR* Unicode;

	cchUnicode = MultiByteToWideChar(CP_ACP, 0, ansiiCode, (int)strlen(ansiiCode), NULL, 0);
	Unicode = (WCHAR*)malloc(cchUnicode * sizeof(WCHAR));
	if (Unicode) {
		MultiByteToWideChar(CP_ACP, 0, ansiiCode, (int)strlen(ansiiCode), Unicode, cchUnicode);
		cbUtf8 = WideCharToMultiByte(CP_UTF8, 0, Unicode, cchUnicode, utf8Code, MAX_PATH_LENGTH - 1, NULL, NULL);
		utf8Code[cbUtf8] = '\0';
		free(Unicode);
	}

	return cbUtf8;
}


const char* GetFileName(char* path)
{
	char* dir, * suffix;
	static char filename[MAX_PATH_LENGTH] = { 0 };

	dir = strrchr(path, '\\');
	if (dir) {
		dir++;
		suffix = strrchr(dir, '.');
		if (suffix)
			strncpy_s(filename, MAX_PATH_LENGTH, dir, strlen(dir) - strlen(suffix));
		else
			strcpy_s(filename, MAX_PATH_LENGTH, dir);
	}
	else {
        suffix = strrchr(path, '.');
		if (suffix)
			strncpy_s(filename, MAX_PATH_LENGTH, path, strlen(path) - strlen(suffix));
		else
			strcpy_s(filename, MAX_PATH_LENGTH, path);
	}

	return filename;
}


int main(int argc, char** argv)
{
	int ret = 0, has_subtitle = 0, 
		encode_video = 0, encode_audio = 0, encode_subtitle = 0;
	CopyStream* videoStream = NULL, * audioStream = NULL,
		* coverStream = NULL, * subtitleStream = NULL;
	AVFormatContext* outFileCtx = NULL;
	AVPacket* videoFrame = NULL, * audioFrame = NULL, * subtitleFrame = NULL;
	Codec* subtitleCodec = NULL;
	char video_path[MAX_PATH_LENGTH] = { 0 };
	char audio_path[MAX_PATH_LENGTH] = { 0 };
	char cover_path[MAX_PATH_LENGTH] = { 0 };
	char subtitle_path[MAX_PATH_LENGTH] = { 0 };
	char output_path[MAX_PATH_LENGTH] = { 0 };

	if (argc == 5 || argc == 6) {
		A2U(argv[1], video_path);
		A2U(argv[2], audio_path);
		A2U(argv[3], cover_path);
		if (argc == 6) {
			A2U(argv[4], subtitle_path);
			has_subtitle = 1;
		}
		A2U(argv[argc - 1], output_path);
	}
	else {
		ret = -1;
		printf("Invalid command\n");
		goto end;
	}

	// 打开输入文件
	ret = read_media(&videoStream, video_path, AVMEDIA_TYPE_VIDEO);
	if (ret < 0) goto end;
	ret = read_media(&audioStream, audio_path, AVMEDIA_TYPE_AUDIO);
	if (ret < 0) goto end;
	ret = read_media(&coverStream, cover_path, AVMEDIA_TYPE_VIDEO);
	if (ret < 0) goto end;

	// 打开输出文件
	ret = write_media(&outFileCtx, output_path);
	if (ret < 0) goto end;

	// 从输入视频中复制容器元数据
	ret = av_dict_copy(&outFileCtx->metadata, videoStream->ctx->metadata, 0);
	if (ret < 0) {
		printf("Failed to copy metadata from video\n");
		goto end;
	}

	// 复制输入文件的流并添加到输出文件中
	ret = add_stream(outFileCtx, videoStream);
	if (ret < 0) goto end;
	ret = add_stream(outFileCtx, audioStream);
	if (ret < 0) goto end;
	ret = add_stream(outFileCtx, coverStream);
	if (ret < 0) goto end;
    
    // 手动设置音频流帧大小 (aac格式)
	audioStream->st_to->codecpar->frame_size = 1024;

	// 读取视频封面
	coverStream->st_to->disposition = AV_DISPOSITION_ATTACHED_PIC;
	ret = read_packet(coverStream, &coverStream->st_to->attached_pic);
	if (ret < 0) {
		printf("Failed to add the attached picture");
		goto end;
	}
	coverStream->st_to->attached_pic.flags |= AV_PKT_FLAG_KEY;

	// 打开字幕及编解码器
	if (has_subtitle) {
		ret = read_media(&subtitleStream, subtitle_path, AVMEDIA_TYPE_SUBTITLE);
		if (ret < 0) goto end;
		ret = open_subtitle_codec(outFileCtx, subtitleStream, &subtitleCodec);
		if (ret < 0) goto end;
		av_dict_set(&subtitleStream->st_to->metadata, "handler_name", GetFileName(subtitle_path), 0);
	}

	// 打印格式信息
	av_dump_format(outFileCtx, 0, output_path, 1);

	// 写文件头
	ret = avformat_write_header(outFileCtx, NULL);
	if (ret < 0) {
		printf("Error occurred when opening output file");
		goto end;
	}

	// 分配内存
	videoFrame = av_packet_alloc();
	audioFrame = av_packet_alloc();
	subtitleFrame = av_packet_alloc();
	if (!(videoFrame && audioFrame && subtitleFrame)) {
		ret = AVERROR(ENOMEM);
		printf("Failed allocating packet buffer\n");
		goto end;
	}

	// 拷贝视频流、音频流等
	ret = write_packet(outFileCtx, &coverStream->st_to->attached_pic);
	if (ret < 0) {
		printf("Error occurred when copying picture\n");
		goto end;
	}
	while (1) {
		if (!encode_video) {
			ret = read_packet(videoStream, videoFrame);
#ifdef DEBUG
			printf("Video Frame: %I64d | %I64d | %I64d (%d)\n", videoFrame->pts, videoFrame->dts, videoFrame->duration, ret);
#endif // DEBUG
			if (ret < 0 && ret != AVERROR_EOF) break;
			encode_video = !ret;
		}
		if (!encode_audio) {
			ret = read_packet(audioStream, audioFrame);
#ifdef DEBUG
			printf("Audio Frame: %I64d | %I64d | %I64d (%d)\n", audioFrame->pts, audioFrame->dts, audioFrame->duration, ret);
#endif // DEBUG
			if (ret < 0 && ret != AVERROR_EOF) break;
			encode_audio = !ret;
		}
		if (has_subtitle && !encode_subtitle) {
			ret = read_packet(subtitleStream, subtitleFrame);
#ifdef DEBUG
			printf("Subtitle Frame: %I64d | %I64d | %I64d (%d)\n", subtitleFrame->pts, subtitleFrame->dts, subtitleFrame->duration, ret);
#endif // DEBUG
			if (ret < 0 && ret != AVERROR_EOF) break;
			encode_subtitle = !ret;
		}
		if (encode_video && (!encode_audio || compare_dts(videoFrame, audioFrame) <= 0)
			&& (!encode_subtitle || compare_dts(videoFrame, subtitleFrame) <= 0)) {
			ret = write_packet(outFileCtx, videoFrame);
			if (ret < 0) break;
			encode_video = 0;
			continue;
		}
		if (encode_audio && (!encode_subtitle || compare_dts(audioFrame, subtitleFrame) <= 0)) {
			ret = write_packet(outFileCtx, audioFrame);
			if (ret < 0) break;
			encode_audio = 0;
			continue;
		}
		if (encode_subtitle) {
			ret = transcode_subtitle(subtitleCodec, subtitleFrame);
			if (ret < 0) break;
			ret = write_packet(outFileCtx, subtitleFrame);
			if (ret < 0) break;
			encode_subtitle = 0;
		}
		else {
			break;
		}
	}
	if (ret < 0 && ret != AVERROR_EOF) {
		printf("Error occurred when copying frames\n");
		goto end;
	}

	// 写文件尾
	ret = av_write_trailer(outFileCtx);
	if (ret < 0) {
		printf("Error occurred when closing output file");
		goto end;
	}

end:
	if (ret < 0) printf("Details: %s (%d)\n", av_err2str(ret), ret);

	// 释放内存
	if (videoStream) stream_free(&videoStream);
	if (audioStream) stream_free(&audioStream);
	if (coverStream) stream_free(&coverStream);
	if (subtitleStream) stream_free(&subtitleStream);
	if (subtitleCodec) codec_free(&subtitleCodec);
	if (outFileCtx) {
		if (!(outFileCtx->oformat->flags & AVFMT_NOFILE))
			avio_closep(&outFileCtx->pb);
		avformat_close_input(&outFileCtx);
	}
	if (videoFrame) av_packet_free(&videoFrame);
	if (audioFrame) av_packet_free(&audioFrame);
	if (subtitleFrame) av_packet_free(&subtitleFrame);

	return ret;
}