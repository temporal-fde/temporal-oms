package com.acme.apps.converters;

import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpOutputMessage;
import org.springframework.http.MediaType;
import org.springframework.http.converter.AbstractHttpMessageConverter;
import org.springframework.lang.Nullable;

import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;

/**
 * Custom HTTP message converter for protobuf messages using JSON format.
 * Deserializes JSON request bodies into protobuf message types.
 */
public class ProtobufJsonHttpMessageConverter extends AbstractHttpMessageConverter<Message> {

    private final JsonFormat.Parser parser = JsonFormat.parser().ignoringUnknownFields();
    private final JsonFormat.Printer printer = JsonFormat.printer().includingDefaultValueFields();

    public ProtobufJsonHttpMessageConverter() {
        super(MediaType.APPLICATION_JSON);
    }

    @Override
    protected boolean supports(Class<?> clazz) {
        return Message.class.isAssignableFrom(clazz);
    }

    @Override
    @Nullable
    protected Message readInternal(Class<? extends Message> clazz, HttpInputMessage inputMessage)
            throws IOException {
        Message.Builder messageBuilder = getMessageBuilder(clazz);
        InputStream inputStream = inputMessage.getBody();
        String json = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
        parser.merge(json, messageBuilder);
        return messageBuilder.build();
    }

    @Override
    protected void writeInternal(Message message, HttpOutputMessage outputMessage)
            throws IOException {
        String json = printer.print(message);
        outputMessage.getBody().write(json.getBytes(StandardCharsets.UTF_8));
    }

    private Message.Builder getMessageBuilder(Class<? extends Message> clazz) {
        try {
            Method method = clazz.getMethod("newBuilder");
            return (Message.Builder) method.invoke(null);
        } catch (Exception e) {
            throw new IllegalArgumentException(
                "Unable to get builder for protobuf message: " + clazz.getName(), e);
        }
    }
}