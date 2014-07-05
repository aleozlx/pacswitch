package com.aleozlx;
import com.aleozlx.pacswitch.*;

public class Messager extends PacswitchMessager {
	public static void main(String[] args) {
		Messager m=new Messager();
		if(m.connect("public","public")&&m.isAuthenticated()){
			try{ System.out.println(m.send("public","Hello world!")); }
			catch(PacswitchException e){ e.printStackTrace(); }
			finally{ m.close(); }
		}
		else System.out.println("Network error");
	}

	public boolean connect(String userid,String password){
		return super.connect(userid,password,null,"222.69.93.107","messager1.0");
	}

	public String handleMessage(String from, String message){
		System.out.println(String.format("%1$s: %2$s",from,message));
		return "ACK";
	}
}

